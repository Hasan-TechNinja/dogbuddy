from django.contrib import admin
from . models import PetInfo, Event

# Register your models here.

class PetInfoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
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

class EventAdmin(admin.ModelAdmin):
    list_display = (
        'id','organizer', 'title', 'activity', 'location', 'data', 'max_participants', 'cost', 'cancellation_fee', 'required_items', 'created_at'
    )
admin.site.register(Event, EventAdmin)