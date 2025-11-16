from django.shortcuts import render, get_object_or_404
from . models import PetInfo
from . serializers import PetInfoSerializer
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView

# Create your views here.

class PetInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        pet_info = get_object_or_404(PetInfo, owner = user)
        serializer = PetInfoSerializer(pet_info, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def put(self, request):
        user = request.user
        pet_info = get_object_or_404(PetInfo, owner = user)
        serializer = PetInfoSerializer(pet_info, data = request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


