from django.contrib import admin
from . models import Profile

# Register your models here.

class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'name',
        'account_type',
        'dog_name',
        'playfulness_level',
        'location',
        'created_at',
    )
admin.site.register(Profile, ProfileAdmin)