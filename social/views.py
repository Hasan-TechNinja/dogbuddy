from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q
from .models import ChatGroup, ChatMessage, FriendRequest, Friendship, GroupMember, Post, Comment, Share
from .serializers import ChatMessageSerializer, FriendRequestSerializer, FriendshipSerializer, PostSerializer, CommentSerializer, ShareSerializer, UserFriendStatusSerializer, ChatUserListSerializer, ChatGroupListSerializer
from authentication.serializers import ProfileSerializer, UserSerializer
from authentication.models import Profile

class SendFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        to_user_id = request.data.get('to_user_id')
        if not to_user_id:
            return Response({'error': 'to_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user == to_user:
            return Response({'error': 'You cannot send a friend request to yourself'}, status=status.HTTP_400_BAD_REQUEST)

        if Friendship.objects.filter(Q(user1=request.user, user2=to_user) | Q(user1=to_user, user2=request.user)).exists():
            return Response({'error': 'You are already friends'}, status=status.HTTP_400_BAD_REQUEST)

        if FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
            return Response({'error': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)
        
        if FriendRequest.objects.filter(from_user=to_user, to_user=request.user).exists():
             return Response({'error': 'This user has already sent you a friend request. Please accept it.'}, status=status.HTTP_400_BAD_REQUEST)

        friend_request = FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    
class AcceptFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        friend_request = get_object_or_404(FriendRequest, from_user__id=user_id, to_user=request.user)

        # Create Friendship
        Friendship.objects.create(user1=friend_request.from_user, user2=friend_request.to_user)
        
        # Delete the request
        friend_request.delete()

        return Response({'message': 'Friend request accepted'}, status=status.HTTP_200_OK)


class RejectFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        friend_request = get_object_or_404(FriendRequest, from_user__id=user_id, to_user=request.user)

        friend_request.delete()
        return Response({'message': 'Friend request rejected'}, status=status.HTTP_200_OK)


class CancelFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        # Find a friend request between these two users (sent by current user or received from user_id)
        friend_request = FriendRequest.objects.filter(
            Q(from_user=request.user, to_user__id=user_id) |
            Q(from_user__id=user_id, to_user=request.user)
        ).first()

        if not friend_request:
            return Response({'error': "Friend request not found"}, status=status.HTTP_404_NOT_FOUND)

        friend_request.delete()
        return Response({'message': "Friend request cancelled"}, status=status.HTTP_200_OK)


class UnfriendView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        friendship = Friendship.objects.filter(
            Q(user1=request.user, user2=other_user) | Q(user1=other_user, user2=request.user)
        ).first()

        if not friendship:
            return Response({'error': 'You are not friends with this user'}, status=status.HTTP_400_BAD_REQUEST)

        friendship.delete()
        return Response({'message': 'Unfriended successfully'}, status=status.HTTP_200_OK)

class FriendListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        friendships = Friendship.objects.filter(Q(user1=request.user) | Q(user2=request.user))
        friends = []
        for friendship in friendships:
            if friendship.user1 == request.user:
                friends.append(friendship.user2)
            else:
                friends.append(friendship.user1)
        
        serializer = UserSerializer(friends, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class GeneralUserListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        users = Profile.objects.filter(account_type='normal')
        serializer = ProfileSerializer(users, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class UserFriendStatusListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Exclude self + only users who completed dog profile setup
        profiles = Profile.objects.exclude(user=request.user).filter(
            has_dog_profile=True
        )

        serializer = UserFriendStatusSerializer(
            profiles,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        profile = get_object_or_404(Profile, user__id=user_id)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class PendingRequestsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        requests = FriendRequest.objects.filter(to_user=request.user)
        serializer = FriendRequestSerializer(requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        serializer = PostSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save(user = request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        post = Post.objects.filter(user = request.user)
        serializer = PostSerializer(post, many = True, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class AllPostsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        posts = Post.objects.all().order_by("-created_at")
        serializer = PostSerializer(posts, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        post = get_object_or_404(Post, id=id, user=request.user)
        serializer = PostSerializer(post, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        post = get_object_or_404(Post, id=id, user=request.user)
        serializer = PostSerializer(post, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PostCommentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        post_serializer = PostSerializer(post, context={"request": request})

        comments = Comment.objects.filter(post=post).order_by("-created_at")
        comment_serializer = CommentSerializer(comments, many=True)

        data = {
            "post": post_serializer.data,
            "comments": comment_serializer.data
        }

        return Response(data, status=status.HTTP_200_OK)


class LikePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        if request.user in post.likes.all():
            post.likes.remove(request.user)
            return Response({"message": "Unliked"}, status=status.HTTP_200_OK)
        else:
            post.likes.add(request.user)
            return Response({"message": "Liked"}, status=status.HTTP_200_OK)


class CommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        comments = Comment.objects.filter(post=post).order_by("-created_at")
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SharePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        # prevent duplicate shares
        existing = Share.objects.filter(user=request.user, post=post).first()
        if existing:
            return Response({"message": "Already shared"}, status=status.HTTP_200_OK)

        share = Share.objects.create(user=request.user, post=post)
        serializer = ShareSerializer(share)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, chat_partner_id):
        chat_partner = get_object_or_404(User, id=chat_partner_id)
        messages = ChatMessage.objects.filter(
            (Q(sender=request.user) & Q(receiver=chat_partner)) |
            (Q(sender=chat_partner) & Q(receiver=request.user))
        ).order_by("timestamp")
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CreateGroup(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        name = request.data.get("name")
        image = request.data.get('image')
        if not name:
            return Response({"error": "Name required"}, status=400)

        group = ChatGroup.objects.create(name=name, image=image)
        GroupMember.objects.create(group=group, user=request.user)
        return Response({
            "group_id": group.id,
            "name": group.name,
            "image": request.build_absolute_uri(group.image.url) if group.image else None,
            "admin": request.user.username
            }, status=201)


class JoinGroup(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id):
        try:
            group = ChatGroup.objects.get(id=group_id)
        except:
            return Response({"error": "Group not found"}, status=404)

        GroupMember.objects.get_or_create(group=group, user=request.user)
        return Response({"message": "Joined"})


class GroupMembers(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        try:
            group = ChatGroup.objects.get(id=group_id)
        except:
            return Response({"error": "Group not found"}, status=404)

        members = GroupMember.objects.filter(group=group).select_related("user")
        member_list = [{"id": m.user.id, "username": m.user.username} for m in members]
        return Response({"members": member_list})
    

class RemoveGroupMemberView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            group = ChatGroup.objects.get(id=group_id)
        except ChatGroup.DoesNotExist:
            return Response({"error": "Group not found"}, status=404)

        try:
            member = GroupMember.objects.get(group=group, user__id=user_id)
        except GroupMember.DoesNotExist:
            return Response({"error": "User is not a member of this group"}, status=404)

        member.delete()
        return Response({"message": "Member removed successfully"}, status=200)
    

class UserPostListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        posts = Post.objects.filter(user=user).order_by("-created_at")
        serializer = PostSerializer(posts, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class MyGroupsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        memberships = GroupMember.objects.filter(user=request.user).select_related("group")
        groups = [m.group for m in memberships]
        serializer = ChatGroupListSerializer(groups, many=True, context={"request": request})
        return Response({"groups": serializer.data}, status=status.HTTP_200_OK)
    

class MyChatUsersListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Fetch users who have had a chat with the current user
        chat_partners = User.objects.filter(
            Q(sent_messages__receiver=user) | Q(received_messages__sender=user)
        ).distinct()

        # Filter out self
        chat_partners = chat_partners.exclude(id=user.id)

        # Map to profiles
        profiles = Profile.objects.filter(user__in=chat_partners)

        serializer = ChatUserListSerializer(
            profiles,
            many=True,
            context={"request": request}
        )

        return Response(
            {"users": serializer.data},
            status=status.HTTP_200_OK
        )