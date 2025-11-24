from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

SIZE_CHOICES = [
    ('small', 'Small'),
    ('medium', 'Medium'),
    ('large', 'Large'),
]

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
]

DOG_MODE = [
    ('snooze', 'Snooze'),
    ('walking', 'Walking'),
    ('playing', 'Playing')
]

class PetInfo(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    playfulness_level = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(100)])
    location = models.CharField(max_length=255, blank=True, null=True)
    weight = models.PositiveIntegerField(default=0)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='medium')
    age = models.CharField(max_length=10, default=0)
    medical_records = models.FileField(upload_to='medical_records/', null=True, blank=True)
    adoption_documents = models.FileField(upload_to='adoption_documents/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=20, choices=DOG_MODE, default='snooze')
    stars = models.ManyToManyField(User, related_name="starred_pets", blank=True)
    points = models.PositiveIntegerField(default=0,)
    image = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    image1 = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    image2 = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    image3 = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    image4 = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name