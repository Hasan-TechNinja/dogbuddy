from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date
from datetime import date
from dateutil.relativedelta import relativedelta

# Create your models here.

SIZE_CHOICES = [
    ('Small', 'Small'),
    ('Medium', 'Medium'),
    ('Large', 'Large'),
]

GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
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
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='Medium')
    date_of_birth = models.DateField(auto_now_add=False, blank=True, null=True)
    breed = models.CharField(max_length=100, blank=True, null=True)
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

    def save(self, *args, **kwargs):
        if self.gender:
            self.gender = self.gender.capitalize()
        if self.size:
            self.size = self.size.capitalize()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    @property
    def friendly_age(self):
        """
        Returns age as a friendly string:
        - 0-11 months  → "3 months", "1 month", "0 months"
        - 12+ months   → "1 year", "1.5 years", "2 years", "2.5 years", ...
        """
        if not self.date_of_birth:
            return None

        today = date.today()
        birth = self.date_of_birth

        years = today.year - birth.year
        months = today.month - birth.month
        days = today.day - birth.day

        # Adjust if birthday hasn't occurred this year
        if (months, days) < (0, 0):
            years -= 1
            months += 12

        # Total months since birth
        total_months = years * 12 + months

        if total_months < 12:
            # 0–11 months
            if total_months == 0:
                return "0 months"
            elif total_months == 1:
                return "1 month"
            else:
                return f"{total_months} months"
        else:
            # 12+ months → show in years (with .5 steps)
            years_decimal = total_months / 12

            # Round to nearest 0 or 0.5
            years_part = int(years_decimal)
            decimal_part = years_decimal - years_part

            if decimal_part < 0.25:
                display = years_part
            elif decimal_part < 0.75:
                display = years_part + 0.5
            else:
                display = years_part + 1

            # Format nicely
            if display == 1:
                return "1 year"
            elif isinstance(display, float):
                return f"{display:.1f} years"
            else:
                return f"{display} years"
    
    @property
    def age_in_months(self):
        """Return age in total months."""
        if not self.date_of_birth:
            return None
        
        today = date.today()
        delta = relativedelta(today, self.date_of_birth)
        return delta.years * 12 + delta.months
    
    @property
    def life_stage(self):
        """Determine life stage based on age and size"""
        age_months = self.age_in_months
        
        if age_months is None:
            return None
        
        # Life stage varies by size
        if self.size == 'Small':
            if age_months < 12:
                return 'Puppy'
            elif age_months < 84:  # 7 years
                return 'Adult'
            else:
                return 'Senior'
        elif self.size == 'Medium':
            if age_months < 12:
                return 'Puppy'
            elif age_months < 84:  # 7 years
                return 'Adult'
            else:
                return 'Senior'
        else:  # Large
            if age_months < 15:
                return 'Puppy'
            elif age_months < 72:  # 6 years
                return 'Adult'
            else:
                return 'Senior'
    

class Event(models.Model):
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    title = models.CharField(max_length=200)
    activity = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    data = models.DateTimeField()
    max_participants = models.PositiveIntegerField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cancellation_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    required_items = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    enrolled_pets = models.ManyToManyField(PetInfo, related_name='events', blank=True)

    def __str__(self):
        return self.title