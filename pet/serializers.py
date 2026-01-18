from rest_framework import serializers
from pet.models import PetInfo
from .models import DOG_MODE, Event


class PetInfoSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    life_stage = serializers.ReadOnlyField()
    owner_name = serializers.SerializerMethodField()
    owner_id = serializers.ReadOnlyField(source='owner.id')

    class Meta:
        model = PetInfo
        fields = "__all__"
        read_only_fields = ["id", "owner"]

    def get_owner_name(self, obj):
        from authentication.models import Profile
        profile = Profile.objects.filter(user=obj.owner).first()
        if profile and profile.name:
            return profile.name
        # return obj.owner.username

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
    name = serializers.CharField(source="organizer.profile.name", read_only=True)
    profile_image = serializers.SerializerMethodField()
    enrolled = serializers.SerializerMethodField()
    class Meta: 
        model = Event
        fields = "__all__"
        read_only_fields = ["organizer", "created_at"]


    def get_profile_image(self, obj):
        request = self.context.get('request') if self.context else None
        post_user = obj.organizer
        profile = getattr(post_user, 'profile', None)
        image_url = None

        if profile:
            acct = getattr(profile, 'account_type', 'normal')
            if acct == 'normal':
                pet = PetInfo.objects.filter(owner=post_user).order_by('-created_at').first()
                if pet and getattr(pet, 'image', None):
                    image_url = pet.image.url
                elif getattr(profile, 'profile_image', None):
                    image_url = profile.profile_image.url
            else:
                if getattr(profile, 'profile_image', None):
                    image_url = profile.profile_image.url

        if image_url and request:
            # return request.build_absolute_uri(image_url)
            return request.build_absolute_uri(image_url)
        return image_url
    

    def get_enrolled(self, obj):
        """Return True if current user is enrolled in this event."""
        request = self.context.get('request') if self.context else None
        if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
            return False
        
        # Adjust according to your model relation:
        # assuming you have a ManyToMany field like `participants = models.ManyToManyField(User, related_name="events")`
        return obj.enrolled_pets.filter(owner=request.user).exists()