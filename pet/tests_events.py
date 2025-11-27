from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import PetInfo, Event
from django.utils import timezone

class EventEnrollmentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)
        
        self.pet = PetInfo.objects.create(
            owner=self.user,
            name='Buddy',
            species='Dog', # Assuming species field exists or is not required based on models.py read earlier, actually it wasn't there but let's check models.py again if needed. Wait, models.py didn't have species. It had size, gender etc.
            # Let's use valid fields from models.py
            size='medium',
            gender='male'
        )
        
        self.organizer = User.objects.create_user(username='organizer', password='password')
        self.event = Event.objects.create(
            organizer=self.organizer,
            title='Dog Park Meetup',
            activity='Playing',
            location='Central Park',
            data=timezone.now(),
            max_participants=5
        )

    def test_enroll_pet_success(self):
        response = self.client.post(f'/pet/events/enroll/{self.event.id}/', {'pet_id': self.pet.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.event.enrolled_pets.count(), 1)
        self.assertEqual(self.event.enrolled_pets.first(), self.pet)

    def test_enroll_pet_auto_detect_success(self):
        # User has only one pet, so it should be auto-detected
        response = self.client.post(f'/pet/events/enroll/{self.event.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.event.enrolled_pets.count(), 1)
        self.assertEqual(self.event.enrolled_pets.first(), self.pet)

    def test_enroll_pet_already_enrolled(self):
        self.event.enrolled_pets.add(self.pet)
        response = self.client.post(f'/pet/events/enroll/{self.event.id}/', {'pet_id': self.pet.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enroll_pet_event_full(self):
        self.event.max_participants = 1
        self.event.save()
        
        # Enroll another pet first
        other_user = User.objects.create_user(username='other', password='password')
        other_pet = PetInfo.objects.create(owner=other_user, name='Rex')
        self.event.enrolled_pets.add(other_pet)
        
        response = self.client.post(f'/pet/events/enroll/{self.event.id}/', {'pet_id': self.pet.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unenroll_pet_success(self):
        self.event.enrolled_pets.add(self.pet)
        response = self.client.post(f'/pet/events/unenroll/{self.event.id}/', {'pet_id': self.pet.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.event.enrolled_pets.count(), 0)

    def test_unenroll_pet_not_enrolled(self):
        response = self.client.post(f'/pet/events/unenroll/{self.event.id}/', {'pet_id': self.pet.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enroll_multiple_pets_ambiguity(self):
        # Create another pet for the same user
        PetInfo.objects.create(owner=self.user, name='Max')
        
        # Try to enroll without specifying pet_id
        response = self.client.post(f'/pet/events/enroll/{self.event.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Multiple pets found', str(response.data))

    def test_enroll_invalid_pet_id(self):
        response = self.client.post(f'/pet/events/enroll/{self.event.id}/', {'pet_id': 999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_enroll_pet_not_owned(self):
        other_user = User.objects.create_user(username='other2', password='password')
        other_pet = PetInfo.objects.create(owner=other_user, name='Rocky')
        
        response = self.client.post(f'/pet/events/enroll/{self.event.id}/', {'pet_id': other_pet.id})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
