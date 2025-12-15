from rest_framework import serializers
from django.contrib.auth.models import User
from .models import DogSize, ProfessionalInformation, Profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
    
class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'name', 'account_type', 'phone', 'created_at']

class ProfessionalInformationSerializer(serializers.ModelSerializer):
    dog_size_worked_with = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=DogSize.objects.all()
    )

    class Meta:
        model = ProfessionalInformation
        fields = ['name', 'experience', 'about', 'dog_size_worked_with']
