from django.urls import path
from . import views

urlpatterns = [
    # Define your URL patterns here
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('verify-email/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('login/', views.LoginView.as_view(), name='login'),

]