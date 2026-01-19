from rest_framework import serializers
from pet.models import PetInfo
from .models import DOG_MODE, Event
from datetime import date


class PetInfoSerializer(serializers.ModelSerializer):
    # These will be computed in the model or serializer
    age = serializers.SerializerMethodField()
    friendly_age = serializers.SerializerMethodField()     # new nice string format
    life_stage = serializers.ReadOnlyField()               # assuming model has this

    owner_name = serializers.SerializerMethodField()
    owner_id = serializers.ReadOnlyField(source='owner.id')

    class Meta:
        model = PetInfo
        fields = "__all__"   # or list explicitly if you prefer
        read_only_fields = ["id", "owner", "created_at", "updated_at"]  # add timestamps if they exist

    def get_age(self, obj):
        """Classic whole years (your original logic)"""
        if not obj.date_of_birth:
            return None
        today = date.today()
        years = today.year - obj.date_of_birth.year
        if (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day):
            years -= 1
        return years

    def get_friendly_age(self, obj):
        """Human-friendly age string: 3 months, 1 year, 1.5 years, 2 years, ..."""
        if not obj.date_of_birth:
            return None

        today = date.today()
        birth = obj.date_of_birth

        years = today.year - birth.year
        months = today.month - birth.month
        days = today.day - birth.day

        # Birthday hasn't occurred yet this year
        if (months < 0) or (months == 0 and days < 0):
            years -= 1
            months += 12

        total_months = years * 12 + months

        if total_months < 12:
            if total_months == 0:
                return "0 months"
            elif total_months == 1:
                return "1 month"
            else:
                return f"{total_months} months"
        else:
            whole_years = total_months // 12
            remaining_months = total_months % 12

            if remaining_months < 6:
                unit = "year" if whole_years == 1 else "years"
                return f"{whole_years} {unit}"
            else:
                unit = "year" if whole_years == 0 else "years"
                return f"{whole_years}.5 {unit}"

    def get_owner_name(self, obj):
        from authentication.models import Profile
        profile = Profile.objects.filter(user=obj.owner).first()
        return profile.name if profile and profile.name else obj.owner.username

    def to_internal_value(self, data):
        # Capitalize gender & size if present
        data = data.copy()  # avoid modifying original
        if 'gender' in data and data['gender']:
            data['gender'] = data['gender'].strip().capitalize()
        if 'size' in data and data['size']:
            data['size'] = data['size'].strip().capitalize()
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