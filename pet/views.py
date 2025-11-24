from django.shortcuts import render, get_object_or_404
from . models import PetInfo
from . serializers import PetInfoSerializer, PetStatusSerializer, PetStatusUpdateSerializer
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


class PetStatusView(APIView):

    def get(self, request):
        try:
            pet_info = PetInfo.objects.get(owner=request.user)
        except PetInfo.DoesNotExist:
            return Response({"error": "Pet not found"}, status=404)

        serializer = PetStatusSerializer(pet_info)
        return Response(serializer.data, status=200)


    def put(self, request):
        serializer = PetStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pet_status = serializer.validated_data["pet_status"]

        try:
            pet_info = PetInfo.objects.get(owner=request.user)
        except PetInfo.DoesNotExist:
            return Response({"error": "Pet not found"}, status=404)

        pet_info.status = pet_status
        pet_info.save()

        return Response({"status": pet_info.status}, status=200)

