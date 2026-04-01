from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Create your models here.

ACCOUNT_TYPE_CHOICES = [
    ('normal', 'Normal'),
    ('dog_coach', 'Dog Coach'),
    ('dog_sitter', 'Dog Sitter'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True, null=True)
    account_type = models.CharField(max_length=20,choices=ACCOUNT_TYPE_CHOICES,default='normal')
    phone = models.CharField(max_length=100, blank=True, null=True)
    has_dog_profile = models.BooleanField(default=False, help_text="Indicates if user has completed dog profile setup")
    created_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Auto-set has_dog_profile for coaches and sitters (they don't need dog profiles)
        if self.account_type in ['dog_coach', 'dog_sitter']:
            self.has_dog_profile = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.get_account_type_display()}"

    @property
    def is_profile_complete(self):
        """Check if user has completed required profile setup"""
        if self.account_type in ['dog_coach', 'dog_sitter']:
            return self.has_dog_profile and hasattr(self, 'professional_info')
        return self.has_dog_profile

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_profile')
        ]



class ProfessionalInformation(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='professional_info')
    name = models.CharField(max_length=100)
    experience = models.CharField(max_length=10)
    about = models.TextField(max_length=500)
    dog_size_worked_with = models.CharField(max_length=200, blank=True, null=True, help_text="Comma-separated dog sizes (e.g., 'Small', 'Small, Large', 'Small, Large, Medium')")

    def save(self, *args, **kwargs):
        if self.dog_size_worked_with:
            sizes = [s.strip().capitalize() for s in self.dog_size_worked_with.split(',')]
            self.dog_size_worked_with = ', '.join(sizes)
        super().save(*args, **kwargs)


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_verifications")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    last_sent_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    share_info = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "code"]),
            models.Index(fields=["expires_at"]),
        ]

    def save(self, *args, **kwargs):
        # Set expiration time to 10 minutes from now if not already set
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

class FCMDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_devices')
    fcm_token = models.TextField(unique=True)
    device_type = models.CharField(max_length=10, choices=[('android', 'Android'), ('ios', 'iOS')], default='android')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.device_type} device"