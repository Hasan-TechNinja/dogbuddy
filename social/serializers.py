from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FriendRequest, Friendship, GroupMessage, Post, Comment, Share, ChatMessage
from authentication.serializers import UserSerializer
from authentication.serializers import ProfileSerializer
from django.db.models import Q

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

    class Meta:
        model = Post
        fields = "__all__"
        read_only_fields = ["user"]


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

    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + ['friend_status']

    def get_friend_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return "none"
        
        user = request.user
        other_user = obj.user

        if user == other_user:
            return "self"

        # Check if they are friends
        if Friendship.objects.filter(
            Q(user1=user, user2=other_user) | Q(user1=other_user, user2=user)
        ).exists():
            return "friend"

        # Check if friend request sent
        if FriendRequest.objects.filter(from_user=user, to_user=other_user).exists():
            return "pending"

        # Check if friend request received
        if FriendRequest.objects.filter(from_user=other_user, to_user=user).exists():
            return "received"

        return "none"
