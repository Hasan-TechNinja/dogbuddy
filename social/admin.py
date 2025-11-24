from django.contrib import admin
from .models import Post, Comment, Share, FriendRequest, Friendship

# Register your models here.

class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "text", "tags", "location", "created_at"
    )
admin.site.register(Post, PostAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "post", "text", "created_at"
    )
admin.site.register(Comment, CommentAdmin)


class ShareAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'post', 'created_at'
    )
admin.site.register(Share, ShareAdmin)



class FriendRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'from_user', 'to_user', 'created_at'
    )
admin.site.register(FriendRequest, FriendRequestAdmin)


class FriendshipAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user1', 'user2', 'created_at'
    )
admin.site.register(Friendship, FriendshipAdmin)