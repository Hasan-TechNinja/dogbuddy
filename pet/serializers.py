from rest_framework import serializers
from pet.models import PetInfo

class PetInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetInfo
        fields = "__all__"
        read_only_fields = ["id", "owner"]