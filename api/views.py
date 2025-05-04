from io import BytesIO

import pdfkit
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import FileResponse
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import UserSerializer
from convertors.document_converters import HtmlToPdfConverter

User = get_user_model()


class UserRegistrationView(APIView):
    @extend_schema(
        summary='Регистрация пользователя',
        description='Создаёт нового пользователя с уникальным и валидным email, именем, фамилией и именем пользователя',
        request=UserSerializer,
        responses={
            201: OpenApiResponse(response=UserSerializer, description='Пользователь успешно создан'),
            400: OpenApiResponse(description='Ошибка валидации'),
        }
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'status': 'User created', 'id': user.id}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    @extend_schema(
        summary='Получение информации о пользователе',
        description='Возвращает информацию о пользователе по его ID.',
        responses={
            200: OpenApiResponse(response=UserSerializer, description='Информация о пользователе'),
            404: OpenApiResponse(description='Пользователь не найден'),
        },
    )
    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserListView(APIView):
    @extend_schema(
        summary='Получение информации обо всех пользователях.',
        description='Возвращает список всех зарегистрированных пользователей.',
        responses={
            201: OpenApiResponse(response=UserSerializer(many=True), description='Список всех пользователей.'),
        }
    )
    def get(self, request):
        queryset = User.objects.all()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)


class UserDeleteView(APIView):
    @extend_schema(
        summary='Удаление пользователя.',
        description='Удаляет пользователя по айди.',
        responses={
            200: OpenApiResponse(response=UserSerializer, description='Пользователь успешно удален.'),
            404: OpenApiResponse(description='Пользователь не найден.'),
        }
    )
    def delete(self, request, pk):
        if not pk:
            return Response(
                {'status': 'Айди пользователя не был предоставлен'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response({'status': 'Пользователь удален'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'status': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)


class HtmlToPdfConvertView(APIView):
    @extend_schema(
        tags=['Конвертация файлов'],
        summary='Конвертация HTML в PDF',
        description='Принимает HTML контент в теле POST-запроса',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file_content': {'type': 'string'},
                    'file_name': {'type': 'string'}
                }
            }
        },
        responses={
            200: OpenApiResponse(description='PDF файл'),
            400: OpenApiResponse(description='Некорректные данные'),
            500: OpenApiResponse(description='Ошибка конвертации')
        }
    )
    def post(self, request):
        try:
            converter = HtmlToPdfConverter()
            enhanced_html = converter.get_html_with_styles(
                request.data.get('file_content')
            )

            pdf_bytes = pdfkit.from_string(
                enhanced_html,
                False,
                options=converter.get_options(),
                configuration=converter.config
            )

            pdf_file = SimpleUploadedFile(
                name=f"{request.data.get('file_name', 'document')}.pdf",
                content=pdf_bytes,
                content_type='application/pdf'
            )

            return FileResponse(
                BytesIO(pdf_file.read()),
                as_attachment=True,
                filename=pdf_file.name,
                content_type='application/pdf'
            )
        except Exception as e:
            return Response(
                {'error': 'Ошибка конвертации', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
