from django.urls import path
from . import views

urlpatterns = [
    # Define your URL patterns here
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('verify-email/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name = 'logout'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('resend/otp/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('delete/', views.DeleteAccount.as_view(), name = 'delete-user')

]