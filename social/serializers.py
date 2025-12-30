from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FriendRequest, Friendship, GroupMessage, Post, Comment, Share, ChatMessage
from authentication.serializers import UserSerializer
from authentication.serializers import ProfileSerializer
from django.db.models import Q
from .utils import get_distance_between_locations
from geopy.distance import geodesic


class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'created_at']
        read_only_fields = ['id', 'created_at']

class FriendshipSerializer(serializers.ModelSerializer):
    user1 = UserSerializer(read_only=True)
    user2 = UserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ['id', 'user1', 'user2', 'created_at']

class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    shares_count = serializers.IntegerField(read_only=True)
    liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = "__all__"
        read_only_fields = ["user"]

    def get_liked(self, obj):
        request = self.context.get('request') if self.context else None
        if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
            return False
        return request.user in obj.likes.all()


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ["post", "user"]


class ShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share
        fields = "__all__"
        read_only_fields = ["post", "user"]

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "sender", "receiver", "message", "timestamp"]


class GroupMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMessage
        fields = ["id", "group", "sender", "message", "timestamp"]


class UserFriendStatusSerializer(ProfileSerializer):
    friend_status = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    location = serializers.CharField(read_only=True)
    profile_image_url = serializers.SerializerMethodField()

    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + [
            'friend_status', 'distance', 'location', 'profile_image_url'
        ]

    def get_profile_image_url(self, obj):
        request = self.context.get('request')
        if obj.profile_image and request:
            return request.build_absolute_uri(obj.profile_image.url)
        return None

    def get_distance(self, obj):
        request = self.context.get('request')
        user_profile = getattr(request.user, 'profile', None)
        if not user_profile or not user_profile.location or not obj.location:
            return None
        return get_distance_between_locations(user_profile.location, obj.location)

    def get_friend_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return "none"

        user = request.user
        other_user = obj.user

        if user == other_user:
            return "self"

        if Friendship.objects.filter(
            Q(user1=user, user2=other_user) | Q(user1=other_user, user2=user)
        ).exists():
            return "friend"

        if FriendRequest.objects.filter(from_user=user, to_user=other_user).exists():
            return "pending"

        if FriendRequest.objects.filter(from_user=other_user, to_user=user).exists():
            return "received"

        return "none"
