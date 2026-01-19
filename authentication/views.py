from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from pet.serializers import PetInfoSerializer
from .models import Profile, EmailVerification, ProfessionalInformation
from social.models import FriendRequest, Friendship
from pet.models import PetInfo
from .serializers import ProfessionalInformationSerializer, ProfileSerializer, UserSerializer
from django.contrib.auth.models import User
import random
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

# Create your views here.

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Professional info
        professional_info = None
        if profile.account_type in ['dog_coach', 'dog_sitter']:
            professional_info = ProfessionalInformation.objects.filter(profile=profile).first()

        # Pets owned by the user``
        pets = PetInfo.objects.filter(owner=request.user)
        pet_serializer = PetInfoSerializer(pets, many=True)

        # Base profile data
        serializer = ProfileSerializer(profile, context={'request': request})
        data = serializer.data

        # Add extra fields
        data['professional_information'] = (
            ProfessionalInformationSerializer(professional_info).data if professional_info else None
        )
        data['pets'] = pet_serializer.data  # list of pets with name + location

        # Optional: derive general location (e.g. from first pet or profile)
        data['dog_home_location'] = (
            pets.first().location if pets.exists() and pets.first().location else getattr(profile, 'location', None)
        )

        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class RegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        set_password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        account_type = request.data.get('type')
        
        # Get common fields for all account types
        name = request.data.get('name')
        phone = request.data.get('phone')
        share_info = request.data.get('share_info', False)  # Default to False if not provided

        if not email or not set_password or not confirm_password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if set_password != confirm_password:
            return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_password(set_password)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)


        if account_type not in ['normal', 'dog_coach', 'dog_sitter']:
            return Response({'error': 'Invalid account type.'}, status=status.HTTP_400_BAD_REQUEST)

        existing = User.objects.filter(email=email).first()
        if existing:
            if existing.is_active:
                return Response({'error': 'Email already in use.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                existing.delete()

        user = User.objects.create_user(username=email, email=email, password=set_password)
        user.is_active = False
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.account_type = account_type
        
        # Set common fields
        if name:
            profile.name = name
        if phone:
            profile.phone = phone

        if account_type == 'normal':
            # For normal users, we no longer auto-create dog profile during registration
            # They will create it manually after login
            # Just save the profile without dog data
            pass

        if account_type in ['dog_coach', 'dog_sitter']:
            professional_name = request.data.get('professional_name')
            experience = request.data.get('experience')
            dog_size_worked_with = request.data.get('dog_size_worked_with')
            about = request.data.get('about')

            if professional_name is None:
                return Response({'error': 'Professional name is required for this account type.'}, status=status.HTTP_400_BAD_REQUEST)
            if experience is None:
                return Response({'error': 'Experience is required for this account type.'}, status=status.HTTP_400_BAD_REQUEST)
            if dog_size_worked_with is None:
                return Response({'error': 'Dog size worked with is required for this account type.'}, status=status.HTTP_400_BAD_REQUEST)
            if about is None:
                return Response({'error': 'About is required for this account type.'}, status=status.HTTP_400_BAD_REQUEST)

            # If dog_size_worked_with is a list, convert to comma-separated string
            if isinstance(dog_size_worked_with, list):
                dog_size_worked_with = ', '.join(dog_size_worked_with)

            professional_info = ProfessionalInformation.objects.create(
                profile=profile,
                name=professional_name,
                experience=experience,
                about=about,
                dog_size_worked_with=dog_size_worked_with
            )


        profile.save()

        code = random.randint(10000, 99999)

        send_mail(
            subject='Verify your email address',
            message=f'Your verification code is {code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        EmailVerification.objects.create(user=user, code=code, share_info=share_info)
        return Response({'message': 'User registered successfully, please verify your email.'}, status=status.HTTP_201_CREATED)



class EmailVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        try:
            user = User.objects.get(email = email)
            email_verification = EmailVerification.objects.get(user = user, code = code)

            # Check if OTP is expired
            if email_verification.is_expired():
                email_verification.delete()
                return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

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
            
            user_id = user.id
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Get user profile data
            profile = Profile.objects.filter(user=user).first()
            profile_data = None
            profile_serializer = ProfileSerializer(profile, context={'request': request})
            profile_data = profile_serializer.data

            return Response({
                'user_id': user_id,
                'refresh': str(refresh),
                'access': access_token,
                'profile': profile_data
            }, status=status.HTTP_200_OK)
                
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
        

class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create a RefreshToken instance and blacklist it
            token = RefreshToken(refresh_token)
            token.blacklist()  # This adds the token to the blacklist

            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK
            )

        except TokenError as e:
            # Handles invalid, expired, or already blacklisted tokens
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'An error occurred during logout.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            
            # Check if there's an existing OTP record
            email_verification = EmailVerification.objects.filter(user=user).first()
            
            if email_verification:
                # Check cooldown period (60 seconds)
                if email_verification.last_sent_at:
                    time_since_last_send = timezone.now() - email_verification.last_sent_at
                    if time_since_last_send < timedelta(seconds=60):
                        remaining_seconds = 60 - int(time_since_last_send.total_seconds())
                        return Response(
                            {'error': f'Please wait {remaining_seconds} seconds before requesting another OTP.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS
                        )
            
            # Generate new OTP code
            code = random.randint(10000, 99999)

            # Send email
            try:
                send_mail(
                    subject='OTP Verification Code',
                    message=f'Your verification code is {code}. This code will expire in 10 minutes.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                return Response({'error': 'Failed to send email. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Update or create EmailVerification record
            # Note: We need to manually set expires_at because update_or_create with defaults won't trigger save()
            if email_verification:
                email_verification.code = code
                email_verification.expires_at = timezone.now() + timedelta(minutes=10)
                email_verification.last_sent_at = timezone.now()
                email_verification.save()
            else:
                EmailVerification.objects.create(user=user, code=code)

            return Response({'message': 'OTP sent successfully to your email.'}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'Email not found.'}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    permission_classesn = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
            code = random.randint(10000, 99999)

            send_mail(
                subject='Password Reset Request',
                message=f'Your password reset code is {code}. This code will expire in 10 minutes.',
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
            
            # Check if OTP is expired
            if email_verification.is_expired():
                email_verification.delete()
                return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
            
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
    

class DeleteAccount(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        
        return Response({'message': 'Account deleted successfully.'},status=status.HTTP_204_NO_CONTENT)
    


class ProfileDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            profile = Profile.objects.get(user__id=id)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Professional info
        professional_info = None
        if profile.account_type in ['dog_coach', 'dog_sitter']:
            professional_info = ProfessionalInformation.objects.filter(profile=profile).first()

        # Pets owned by the profile owner
        pets = PetInfo.objects.filter(owner=profile.user)
        pet_serializer = PetInfoSerializer(pets, many=True)

        # Base profile data
        serializer = ProfileSerializer(profile, context={'request': request})
        data = serializer.data

        # Add extra fields
        data['professional_information'] = (
            ProfessionalInformationSerializer(professional_info).data if professional_info else None
        )
        data['pets'] = pet_serializer.data

        # ── Improved friendship status ───────────────────────────────────────
        current_user = request.user
        other_user = profile.user

        if current_user == other_user:
            friend_status = "self"
        elif Friendship.objects.filter(
            Q(user1=current_user, user2=other_user) |
            Q(user1=other_user, user2=current_user)
        ).exists():
            friend_status = "friend"
        elif FriendRequest.objects.filter(
            from_user=current_user, to_user=other_user
        ).exists():
            friend_status = "pending"
        elif FriendRequest.objects.filter(
            from_user=other_user, to_user=current_user
        ).exists():
            friend_status = "received"
        else:
            friend_status = "none"

        data['friend_status'] = friend_status
        # Optional: keep is_friend for backward compatibility (or remove it)
        data['is_friend'] = (friend_status == "friend")

        # Location fallback
        data['dog_home_location'] = (
            pets.first().location if pets.exists() and pets.first().location
            else getattr(profile, 'location', None)
        )

        return Response(data, status=status.HTTP_200_OK)