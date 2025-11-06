from django.shortcuts import render
from .models import Profile
from .serializers import UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions


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
        

    def put(self, reqeust):
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