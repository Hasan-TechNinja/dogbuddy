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



class ProfessionalInformation(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='professional_info')
    name = models.CharField(max_length=100)
    experience = models.CharField(max_length=10)
    about = models.TextField(max_length=500)
    dog_size_worked_with = models.CharField(max_length=200, blank=True, null=True, help_text="Comma-separated dog sizes (e.g., 'small', 'small, large', 'small, large, medium')")


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