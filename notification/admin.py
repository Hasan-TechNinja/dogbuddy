from django.contrib import admin
from . models import FCMDevice, Notification

# Register your models here.

class FCMDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'created_at')
    list_filter = ('device_type',)
    search_fields = ('user__username', 'fcm_token')
    ordering = ('-created_at',)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('user__username', 'title', 'body')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
admin.site.register(FCMDevice, FCMDeviceAdmin)
admin.site.register(Notification, NotificationAdmin)