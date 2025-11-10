from django.db import models
from django.contrib.auth.models import User

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

class PetInfo(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    weight = models.PositiveIntegerField(default=0)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    medical_records = models.FileField(upload_to='medical_records/', null=True, blank=True)
    adoption_documents = models.FileField(upload_to='adoption_documents/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    image = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    image2 = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    image3 = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    image4 = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    image5 = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    image6 = models.ImageField(upload_to='pet_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name