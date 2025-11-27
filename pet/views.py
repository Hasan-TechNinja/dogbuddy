from django.shortcuts import render, get_object_or_404
from . models import PetInfo, Event
from . serializers import PetInfoSerializer, PetStatusSerializer, PetStatusUpdateSerializer, EventSerializer
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


class EventCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = EventSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save(organizer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class EventListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        events = Event.objects.all()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class EventEnrollView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        user = request.user
        pet_id = request.data.get('pet_id')

        if pet_id:
            pet = get_object_or_404(PetInfo, id=pet_id, owner=user)
        else:
            pets = PetInfo.objects.filter(owner=user)
            if pets.count() == 1:
                pet = pets.first()
            elif pets.count() > 1:
                return Response({"detail": "Multiple pets found. Please specify pet_id."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail": "No pets found for this user."}, status=status.HTTP_404_NOT_FOUND)

        if event.enrolled_pets.filter(id=pet.id).exists():
            return Response({"detail": "Pet already enrolled in this event."}, status=status.HTTP_400_BAD_REQUEST)

        if event.enrolled_pets.count() >= event.max_participants:
            return Response({"detail": "Event has reached maximum participants."}, status=status.HTTP_400_BAD_REQUEST)

        event.enrolled_pets.add(pet)
        event.save()

        return Response({"detail": "Pet enrolled successfully."}, status=status.HTTP_200_OK)
    

class EventUnenrollView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        user = request.user
        pet_id = request.data.get('pet_id')

        if pet_id:
            pet = get_object_or_404(PetInfo, id=pet_id, owner=user)
        else:
            pets = PetInfo.objects.filter(owner=user)
            if pets.count() == 1:
                pet = pets.first()
            elif pets.count() > 1:
                return Response({"detail": "Multiple pets found. Please specify pet_id."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail": "No pets found for this user."}, status=status.HTTP_404_NOT_FOUND)

        if not event.enrolled_pets.filter(id=pet.id).exists():
            return Response({"detail": "Pet is not enrolled in this event."}, status=status.HTTP_400_BAD_REQUEST)

        event.enrolled_pets.remove(pet)
        event.save()

        return Response({"detail": "Pet unenrolled successfully."}, status=status.HTTP_200_OK)
    

class EventDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            event = Event.objects.get(id=id)
        except Event.DoesNotExist:
            return Response(
                {"error": "Event not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CancelEventView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, event_id):
        event = get_object_or_404(Event, id = event_id, organizer = request.user)
        event.delete()
        return Response({'detail': 'Event cancelled successfully.'}, status=status.HTTP_200_OK)
    

class MyEventsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(organizer = request.user)
        serializer = EventSerializer(events, many = True)

        return Response(serializer.data, status=status.HTTP_200_OK)