from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('register/', views.register, name='register'),

    path('base/', views.base_page, name='base'),
    path('database/', views.database_info, name='database_info'),
    path('upload/', views.upload_document, name='upload_document'),
    path('delete_document/<uuid:document_uuid>/', views.delete_document, name='delete_document'),
    path('give_access/<uuid:document_uuid>/', views.give_access, name='give_access'),
    path('user-search/', views.user_search, name='user_search'),
    path('document/<uuid:uuid>/', views.document_detail, name='document_detail'),
    path('profile/', views.profile, name='profile'),

    path('html-to-pdf/', views.html_to_pdf, name='html_to_pdf'),
    path('word-to-pdf/', views.word_to_pdf, name='word_to_pdf'),
    path('pdf_to_word/', views.pdf_to_word, name='pdf_to_word'),
    path('image_to_pdf/', views.image_to_pdf, name='image_to_pdf'),
    path('image_to_grayscale/', views.image_to_grayscale, name='image_to_grayscale'),
    path('png_to_jpg/', views.png_to_jpg, name='png_to_jpg'),
    path('bmp_to_jpg/', views.bmp_to_jpg, name='bmp_to_jpg'),
    path('image_distort/', views.image_distort, name='image_distort'),
]
