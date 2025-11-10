from django.contrib import admin
from . models import PetInfo

# Register your models here.

class PetInfoAdmin(admin.ModelAdmin):
    list_display = (
        'owner',
        'name',
        'playfulness_level',
        'location',
        'weight',
        'size',
        'gender',
        'created_at',
    )
admin.site.register(PetInfo, PetInfoAdmin)