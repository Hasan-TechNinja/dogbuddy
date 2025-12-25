from rest_framework import serializers
from pet.models import PetInfo
from .models import DOG_MODE, Event


class PetInfoSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    life_stage = serializers.ReadOnlyField()
    class Meta:
        model = PetInfo
        fields = "__all__"
        read_only_fields = ["id", "owner"]

    def to_internal_value(self, data):
        if 'gender' in data and data['gender']:
            data['gender'] = data['gender'].capitalize()
        if 'size' in data and data['size']:
            data['size'] = data['size'].capitalize()
        return super().to_internal_value(data)


class PetStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetInfo
        fields = ["status"]

class PetStatusUpdateSerializer(serializers.Serializer):
    pet_status = serializers.ChoiceField(choices=DOG_MODE)


class EventSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Event
        fields = "__all__"
        read_only_fields = ["organizer", "created_at"]