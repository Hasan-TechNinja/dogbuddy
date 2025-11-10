from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

ACCOUNT_TYPE_CHOICES = [
    ('normal', 'Normal'),
    ('dog_coach', 'Dog Coach'),
    ('dog_sitter', 'Dog Sitter'),
]

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True, null=True)
    account_type = models.CharField(max_length=20,choices=ACCOUNT_TYPE_CHOICES,default='normal')
    phone = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_account_type_display()}"

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_profile')
        ]

DOG_SIZE_CHOICES = [
    ('small', 'Small'),
    ('medium', 'Medium'),
    ('large', 'Large'),
    ('all', 'All')
]
class ProfessionalInformation(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='professional_info')
    name = models.CharField(max_length=100)
    experience = models.CharField(max_length=10)
    about = models.TextField(max_length=500)
    dog_size_worked_with = models.CharField(max_length=50, choices=DOG_SIZE_CHOICES, default='all')


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

    def is_expired(self):
        return timezone.now() > self.expires_at