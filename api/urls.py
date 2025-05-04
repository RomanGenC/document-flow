from django.urls import path

from api import views

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('user/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('delete/<int:pk>', views.UserDeleteView.as_view(), name='user-delete'),

    path('convert/html-to-pdf/', views.HtmlToPdfConvertView.as_view(), name='api_html_to_pdf'),
]
