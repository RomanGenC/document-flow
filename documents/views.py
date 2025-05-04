from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from convertors.document_converters import (
    HtmlToPdfConverter,
    WordToPdfConverter,
    ImageToPdfConverter,
    ImageToGrayscaleConverter, ImageToDistortConverter, PngToJpgConverter, BmpToJpgConverter
)
from utils.pdf.generate_pdf import convert_word_to_pdf_v2
from .forms import DocumentForm, LoginForm, UserRegistrationForm, GiveAccessForm
from .models import Document, DocumentAccess


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
    user = get_object_or_404(User, username=request.user.username)
    document = Document.objects.filter(uuid=document_uuid).first()
    # os.remove(os.path.join(settings.MEDIA_ROOT, 'documents',  f'{document.title}.{document.file_type}'))
    document.delete()

    documents = Document.objects.filter(uploaded_by=user)
    documents_with_unshared_users = []

    for document in documents:
        documents_with_unshared_users.append({
            "document": document,
        })

    return render(
        request,
        'registration/profile.html',
        {'user': user, 'documents_with_unshared_users': documents_with_unshared_users},
    )


def give_access(request, document_uuid):
    document = get_object_or_404(Document, uuid=document_uuid, owner=request.user)

    if request.method == 'POST':
        form = GiveAccessForm(request.POST, document=document)
        if form.is_valid():
            access = form.save(commit=False)
            access.document = document
            access.granted_by = request.user
            access.save()
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
                    return HttpResponse('Вы успешно аунтентифицировались!')
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
