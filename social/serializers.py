from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FriendRequest, Friendship, GroupMessage, Post, Comment, Share, ChatMessage, ChatGroup
from authentication.serializers import UserSerializer
from authentication.serializers import ProfileSerializer
from django.db.models import Q, Max
from django.utils import timezone
from .utils import get_distance_between_locations
from geopy.distance import geodesic
from pet.models import PetInfo
from pet.serializers import PetInfoSerializer


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

    name = serializers.CharField(source="user.profile.name", read_only=True)
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = "__all__"
        read_only_fields = ["user"]

    def get_liked(self, obj):
        request = self.context.get('request') if self.context else None
        if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
            return False
        return request.user in obj.likes.all()

    def get_profile_image(self, obj):
        request = self.context.get('request') if self.context else None
        post_user = obj.user
        profile = getattr(post_user, 'profile', None)
        image_url = None

        if profile:
            acct = getattr(profile, 'account_type', 'normal')
            if acct == 'normal':
                pet = PetInfo.objects.filter(owner=post_user).order_by('-created_at').first()
                if pet and getattr(pet, 'image', None):
                    image_url = pet.image.url
                elif getattr(profile, 'profile_image', None):
                    image_url = profile.profile_image.url
            else:
                if getattr(profile, 'profile_image', None):
                    image_url = profile.profile_image.url

        if image_url and request:
            # return request.build_absolute_uri(image_url)
            return request.build_absolute_uri(image_url)
        return image_url



class CommentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.profile.name", read_only=True)
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ["post", "user"]

    def get_profile_image(self, obj):
        request = self.context.get('request') if self.context else None
        comment_user = obj.user
        profile = getattr(comment_user, 'profile', None)
        image_url = None

        if profile:
            acct = getattr(profile, 'account_type', 'normal')
            if acct == 'normal':
                pet = PetInfo.objects.filter(owner=comment_user).order_by('-created_at').first()
                if pet and getattr(pet, 'image', None):
                    image_url = pet.image.url
                elif getattr(profile, 'profile_image', None):
                    image_url = profile.profile_image.url
            else:
                if getattr(profile, 'profile_image', None):
                    image_url = profile.profile_image.url

        if image_url and request:
            return request.build_absolute_uri(image_url)
        return image_url


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
    sender_name = serializers.CharField(source="sender.profile.name", read_only=True)
    sender_image = serializers.SerializerMethodField()

    class Meta:
        model = GroupMessage
        fields = ["id", "group", "sender", "sender_name", "sender_image", "message", "timestamp"]

    def get_sender_image(self, obj):
        request = self.context.get('request')
        sender = obj.sender
        profile = getattr(sender, 'profile', None)
        if not profile:
            return None
        
        image_url = None
        acct = getattr(profile, 'account_type', 'normal')
        if acct == 'normal':
            pet = PetInfo.objects.filter(owner=sender).order_by('-created_at').first()
            if pet and pet.image:
                image_url = pet.image.url
            elif profile.profile_image:
                image_url = profile.profile_image.url
        else:
            if profile.profile_image:
                image_url = profile.profile_image.url
        
        if image_url and request:
            return request.build_absolute_uri(image_url)
        return image_url


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
        if not request or not request.user.is_authenticated:
            return None
            
        user_profile = getattr(request.user, 'profile', None)
        other_profile = obj
        
        if not user_profile or not other_profile:
            return None
            
        # Try coordinates first
        from .utils import get_distance_between_points
        distance = get_distance_between_points(
            user_profile.latitude, user_profile.longitude,
            other_profile.latitude, other_profile.longitude
        )
        
        if distance is not None:
            return distance
            
        # Fallback to named locations
        if user_profile.location and other_profile.location:
            return get_distance_between_locations(user_profile.location, other_profile.location)
            
        return None

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


class ChatUserListSerializer(UserFriendStatusSerializer):
    unseen_count = serializers.SerializerMethodField()
    last_message_time_ago = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta(UserFriendStatusSerializer.Meta):
        fields = UserFriendStatusSerializer.Meta.fields + ['unseen_count', 'last_message_time_ago', 'last_message', 'profile_image']

    def get_profile_image(self, obj):
        request = self.context.get('request')
        profile_user = obj.user
        image_url = None
        
        acct = getattr(obj, 'account_type', 'normal')
        if acct == 'normal':
            pet = PetInfo.objects.filter(owner=profile_user).order_by('-created_at').first()
            if pet and pet.image:
                image_url = pet.image.url
            elif obj.profile_image:
                image_url = obj.profile_image.url
        else:
            if obj.profile_image:
                image_url = obj.profile_image.url
        
        if image_url and request:
            return request.build_absolute_uri(image_url)
        return image_url

    def get_last_message(self, obj):
        if hasattr(obj, 'last_message_text'):
            return obj.last_message_text
        
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
            
        last_msg = ChatMessage.objects.filter(
            (Q(sender=request.user, receiver=obj.user) | Q(sender=obj.user, receiver=request.user))
        ).order_by('-timestamp').first()
        
        return last_msg.message if last_msg else None

    def get_unseen_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
            
        attr_name = f'unseen_count_{request.user.id}'
        if hasattr(obj, attr_name):
            return getattr(obj, attr_name)
            
        return ChatMessage.objects.filter(
            sender=obj.user,
            receiver=request.user,
            is_read=False
        ).count()

    def get_last_message_time_ago(self, obj):
        if hasattr(obj, 'last_message_time') and obj.last_message_time:
            return self._format_time_ago(obj.last_message_time)

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        last_msg = ChatMessage.objects.filter(
            (Q(sender=request.user, receiver=obj.user) | Q(sender=obj.user, receiver=request.user))
        ).order_by('-timestamp').first()

        if last_msg:
            return self._format_time_ago(last_msg.timestamp)
        return None

    def _format_time_ago(self, dt):
        now = timezone.now()
        diff = now - dt
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)}s ago"
        minutes = seconds / 60
        if minutes < 60:
            return f"{int(minutes)}min ago"
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)}h ago"
        days = hours / 24
        return f"{int(days)}d ago"


class ChatGroupListSerializer(serializers.ModelSerializer):
    unseen_count = serializers.SerializerMethodField()
    last_message_time_ago = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = ChatGroup
        fields = ['id', 'name', 'image', 'unseen_count', 'last_message_time_ago']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_unseen_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        try:
            membership = obj.members.get(user=request.user)
            return obj.messages.filter(
                timestamp__gt=membership.last_read_timestamp
            ).exclude(sender=request.user).count()
        except:
            return 0

    def get_last_message_time_ago(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return self._format_time_ago(last_msg.timestamp)
        return None

    def _format_time_ago(self, dt):
        now = timezone.now()
        diff = now - dt
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)}s ago"
        minutes = seconds / 60
        if minutes < 60:
            return f"{int(minutes)}min ago"
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)}h ago"
        days = hours / 24
        return f"{int(days)}d ago"
