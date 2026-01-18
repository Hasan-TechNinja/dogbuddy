from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ProfessionalInformation, Profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
    
class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_profile_complete = serializers.ReadOnlyField()
    dog_profile_image = serializers.ImageField(read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'name', 'account_type', 'phone', 'profile_image', 'has_dog_profile', 'is_profile_complete', 'created_at', 'dog_profile_image']

class ProfessionalInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalInformation
        fields = ['name', 'experience', 'about', 'dog_size_worked_with']

    def to_internal_value(self, data):
        if 'dog_size_worked_with' in data and data['dog_size_worked_with']:
            sizes = [s.strip().capitalize() for s in data['dog_size_worked_with'].split(',')]
            data['dog_size_worked_with'] = ', '.join(sizes)
        return super().to_internal_value(data)
