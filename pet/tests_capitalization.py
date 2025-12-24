from django.test import TestCase
from django.contrib.auth.models import User
from pet.models import PetInfo
from pet.serializers import PetInfoSerializer
from authentication.models import Profile, ProfessionalInformation
from authentication.serializers import ProfessionalInformationSerializer

class CapitalizationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        # Profile might be created by signals, so use get_or_create or filter
        self.profile, _ = Profile.objects.get_or_create(user=self.user, defaults={'account_type': 'dog_coach'})

    def test_pet_info_model_capitalization(self):
        pet = PetInfo.objects.create(
            owner=self.user,
            name='Buddy',
            gender='female',
            size='medium'
        )
        self.assertEqual(pet.gender, 'Female')
        self.assertEqual(pet.size, 'Medium')

    def test_pet_info_serializer_capitalization(self):
        data = {
            'name': 'Max',
            'gender': 'male',
            'size': 'large'
        }
        serializer = PetInfoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['gender'], 'Male')
        self.assertEqual(serializer.validated_data['size'], 'Large')

    def test_professional_info_model_capitalization(self):
        prof_info = ProfessionalInformation.objects.create(
            profile=self.profile,
            name='Coach Hasan',
            experience='5 years',
            about='I love dogs',
            dog_size_worked_with='small, medium, large'
        )
        self.assertEqual(prof_info.dog_size_worked_with, 'Small, Medium, Large')

    def test_professional_info_serializer_capitalization(self):
        data = {
            'name': 'Sitter Hasan',
            'experience': '3 years',
            'about': 'I am a sitter',
            'dog_size_worked_with': 'small,large'
        }
        serializer = ProfessionalInformationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['dog_size_worked_with'], 'Small, Large')
