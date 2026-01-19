from django.contrib import admin
from . models import Profile, ProfessionalInformation

# Register your models here.

class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'name',
        'account_type',
        # 'dog_name',
        # 'playfulness_level',
        # 'location',
        'created_at',
    )
admin.site.register(Profile, ProfileAdmin)

class ProfessionalInformationAdmin(admin.ModelAdmin):
    list_display = (
        'profile',
        'name',
        'experience',
        'about',
        # 'dog_size_worked_with',
    )
admin.site.register(ProfessionalInformation, ProfessionalInformationAdmin)


admin.site.site_header = 'Dog Buddy Administration'
admin.site.index_title = 'Dog Buddy Admin Portal'
admin.site.site_title = 'Dog Buddy Administration'
    