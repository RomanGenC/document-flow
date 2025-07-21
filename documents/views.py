from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods

from convertors.document_converters import (
    HtmlToPdfConverter,
    WordToPdfConverter,
    ImageToPdfConverter,
    ImageToGrayscaleConverter, ImageToDistortConverter, PngToJpgConverter, BmpToJpgConverter
)
from utils.pdf.generate_pdf import convert_word_to_pdf_v2
from utils.tasks_utils import run_task
from .forms import DocumentForm, LoginForm, UserRegistrationForm, GiveAccessForm
from .models import Document, DocumentAccess
from .tasks import task_send_email

User = get_user_model()


@login_required
def profile(request):
    """Функция для вывода личного кабинета пользователя"""
    user = get_object_or_404(User, username=request.user.username)
    documents = Document.objects.filter(owner=user)
    accessed_documents = DocumentAccess.objects.filter(user=request.user).prefetch_related('document')

    return render(
        request,
        'registration/profile.html',
        {'user': user, 'documents': documents, 'accessed_documents': accessed_documents},
    )


@login_required
def document_detail(request, uuid):
    """Выводит детальную информацию о документе"""
    document = get_object_or_404(Document, uuid=uuid)
    return render(request, 'document/document_detail.html', {'document': document})


def database_info(request):  # ToDo: добавить шаблон
    """Выводит информацию о состоянии базы"""
    return render(request, 'database_info.html')


def get_converter_by_mode(mode: str):
    """Получить конвертер из скрытого html тега"""
    return {
        'html': HtmlToPdfConverter(),
        'word': WordToPdfConverter(),
        'image': ImageToPdfConverter(),
        'image_to_grayscale': ImageToGrayscaleConverter(),
        'png_to_jpg': PngToJpgConverter(),
        'bmp_to_jpg': BmpToJpgConverter(),
        'image_distort': ImageToDistortConverter(),
    }.get(mode)


def send_email_about_document(subject, html_message, user_email, user_id):
    """
    Метод для запуска таска по отправке письма на почту
    :param subject: Заголовок письма
    :param html_message: Текст письма в html
    :param user_email: Почта пользователя, которому будет отправлено письмо
    :param user_id: Id пользователя, которому будет отправлено письмо
    """
    run_task(
        task=task_send_email,
        queue='send_email',
        task_kwargs={
            'subject': subject,
            'html_message': html_message,
            'to': [user_email],
        },
        task_id=f'send_email_about_document_user_id_{user_id}',
        time_limit=60,
    )


@login_required  # ToDo: оптимизировать
def upload_document(request):
    if request.method == 'POST':
        upload_type = request.POST.get('upload_type')
        if upload_type == 'direct':
            form = DocumentForm(request.POST, request.FILES)
            document = form.save(commit=False)
            document.owner = request.user
            document.file_size = document.file.size
            document.file_type = document.file.name.split('.')[-1].lower()
            document.save()
            return redirect('document_detail', uuid=document.uuid)

        mode = request.POST.get('mode')
        document_title = request.POST.get('document_title', 'document')
        convertor = get_converter_by_mode(mode)
        pdf_file = convertor.convert(file_name=document_title, request=request)
        form = DocumentForm({'title': document_title}, {'file': pdf_file})
        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user
            document.file_size = document.file.size
            document.file_type = document.file.name.split('.')[-1]
            document.save()
            if request.user.email:
                send_email_about_document(
                    subject='Документ загружен',
                    html_message='Ваш документ был загружен',
                    user_email=request.user.email,
                    user_id=request.user.id,
                )

            return redirect('document_detail', uuid=document.uuid)
        else:
            print(form.errors)
    else:
        form = DocumentForm()
    return render(request, 'document/upload_document.html', {'form': form})


def get_pdf_from_word(word_file, pdf_file_name, pdf_title):
    # pdf_bytes = convert_word_to_pdf(word_file, pdf_file_name, pdf_title)
    pdf_bytes = convert_word_to_pdf_v2(word_file, pdf_file_name, pdf_title)

    return SimpleUploadedFile(
        pdf_file_name,
        pdf_bytes,
        content_type='application/pdf'
    )


def delete_document(request, document_uuid):
    document = Document.objects.filter(uuid=document_uuid).first()
    # os.remove(os.path.join(settings.MEDIA_ROOT, 'documents',  f'{document.title}.{document.file_type}'))
    document.delete()

    return redirect('profile')


def give_access(request, document_uuid):
    document = get_object_or_404(Document, uuid=document_uuid, owner=request.user)

    if request.method == 'POST':
        form = GiveAccessForm(request.POST, document=document)
        if form.is_valid():
            access = form.save(commit=False)
            access.document = document
            access.granted_by = request.user
            access.save()
            user_for_sending_email = User.objects.filter(id=request.POST['user'][0]).first()
            if user_for_sending_email.email:
                context = {
                    'owner': request.user,
                    'shared_document': document,
                    'site_domain': 'http://127.0.0.1:4545',
                }
                send_email_about_document(
                    subject='С вами поделились документом',
                    html_message=render_to_string('send_email/email_shared_document.html', context),
                    user_email=user_for_sending_email.email,
                    user_id=user_for_sending_email.id,
                )

            return render(request, 'document/document_detail.html', {'document': document})
    else:
        form = GiveAccessForm(document=document)

    return render(request, 'document/give_access.html', {
            'document': document,
            'form': form,
        },
    )


@require_http_methods(["GET"])
def user_search(request):
    search = request.GET.get('q', '')
    page = int(request.GET.get('page', 1))

    users = User.objects.exclude(id=request.user.id).filter(
        Q(username__icontains=search) |
        Q(email__icontains=search)
    ).order_by('username')

    paginator = Paginator(users, 100)
    page_obj = paginator.get_page(page)

    results = [{
        'id': user.id,
        'text': f"{user.username} ({user.email})"
    } for user in page_obj]

    return JsonResponse({
        'results': results,
        'pagination': {'more': page_obj.has_next()}
    })


def base_page(request):
    return render(request, 'base.html')


def html_to_pdf(request):
    return render(request, 'convert/html_to_pdf.html')


def image_to_pdf(request):
    return render(request, 'convert/image_to_pdf.html')


def word_to_pdf(request):
    return render(request, 'convert/word_to_pdf.html')


def pdf_to_word(request):
    return render(request, 'convert/pdf_to_word.html')


def image_to_grayscale(request):
    return render(request, 'convert/image_to_grayscale.html')


def png_to_jpg(request):
    return render(request, 'convert/png_to_jpg.html')


def bmp_to_jpg(request):
    return render(request, 'convert/bmp_to_jpg.html')


def image_distort(request):  # ToDo: починить
    return render(request, 'convert/image_distort.html')


def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(
                request,
                username=cd['username'],
                password=cd['password'],
            )
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return render(request, 'base.html')
                else:
                    return HttpResponse('Аутентификация не прошла!')
            else:
                return HttpResponse('Невалидный аккаунт!')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            return render(
                request,
                'registration/register_done.html',
                {'new_user': new_user},
            )
    else:
        user_form = UserRegistrationForm()
    return render(
        request,
        'registration/register.html',
        {'user_form': user_form},
    )
