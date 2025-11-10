from django.shortcuts import render
from .models import Profile, EmailVerification
from .serializers import UserSerializer
from django.contrib.auth.models import User
import random
from django.core.mail import send_mail

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


# Create your views here.

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            data = {
                'name': profile.name,
                'account_type': profile.account_type,
                'dog_name': profile.dog_name,
                'playfulness_level': profile.playfulness_level,
                'location': profile.location,
                'created_at': profile.created_at,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        

    def put(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            data = request.data

            profile.name = data.get('name', profile.name)
            profile.account_type = data.get('account_type', profile.account_type)
            profile.dog_name = data.get('dog_name', profile.dog_name)
            profile.playfulness_level = data.get('playfulness_level', profile.playfulness_level)
            profile.location = data.get('location', profile.location)
            profile.save()

            return Response({'message': 'Profile updated successfully.'}, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        

class RegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        set_password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        type = request.data.get('type')

        if set_password != confirm_password:
            return Response({'error': 'Password do not match.'}, status = status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():

            user = User.objects.filter(email=email).first()

            if user.is_active:
                return Response({'error': 'Email already in use.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                user.delete()

        if type not in ['normal', 'dog_coach', 'dog_sitter']:
            return Response({'error': 'Invalid account type.'}, status=status.HTTP_400_BAD_REQUEST)
        
            
        user = User.objects.create_user(username=email, email=email, password=set_password)
        user.is_active = False
        user.save()

        profile = Profile.objects.get(user = user)
        profile.account_type = type
        profile.save()

        code = random.randint(10000, 99999)

        send_mail(
            subject='Verify your email address',
            message=f'Your verification code is {code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        EmailVerification.objects.create(user = user, code = code)
        return Response({'message': 'User registered successfully, please verify your email.'}, status=status.HTTP_201_CREATED)
    

class EmailVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        try:
            user = User.objects.get(email = email)
            email_verification = EmailVerification.objects.get(user = user, code = code)

            user.is_active = True
            user.save()
            email_verification.delete()

            return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'Invalid email or code.'}, status=status.HTTP_400_BAD_REQUEST)
        except EmailVerification.DoesNotExist:
            return Response({'error': 'Invalid email or code.'}, status=status.HTTP_400_BAD_REQUEST)
        

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
            if not user.is_active:
                return Response({'error': 'Account is not active. Please verify your email.'}, status=status.HTTP_400_BAD_REQUEST)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'refresh': str(refresh),
                'access': access_token
            }, status=status.HTTP_200_OK)
                
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
        

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blocklist()

            return Response({'message': "Logged out successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        


class PasswordResetRequestView(APIView):
    permission_classesn = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
            code = random.randint(10000, 99999)

            send_mail(
                subject='Password Reset Request',
                message=f'Your password reset code is {code}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            EmailVerification.objects.update_or_create(user=user, defaults={'code': code})

            return Response({'message': 'Password reset code sent to email.'}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'Email not found.'}, status=status.HTTP_400_BAD_REQUEST)
        

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        try:
            user = User.objects.get(email = email)
            email_verification = EmailVerification.objects.get(user = user, code = code)
            if email_verification:
                return Response({'message': 'Code verified successfully. now you can reset your password.'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'Invalid email or code.'}, status=status.HTTP_400_BAD_REQUEST)
        except EmailVerification.DoesNotExist:
            return Response({'error': 'Invalid email or code.'}, status=status.HTTP_400_BAD_REQUEST)
        

class PasswordChangeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')

        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        EmailVerification.objects.filter(user = user).delete()

        return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)