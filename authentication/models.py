from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
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
    dog_name = models.CharField(max_length=100, blank=True, null=True)
    playfulness_level = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(100)])
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_account_type_display()}"

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_profile')
        ]


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_verifications")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    last_sent_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "code"]),
            models.Index(fields=["expires_at"]),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at