from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q
from .models import FriendRequest, Friendship, Post, Comment, Share
from .serializers import FriendRequestSerializer, FriendshipSerializer, PostSerializer, CommentSerializer, ShareSerializer
from authentication.serializers import UserSerializer

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

    def post(self, request, request_id):
        friend_request = get_object_or_404(FriendRequest, id=request_id)

        if friend_request.to_user != request.user:
            return Response({'error': 'You are not authorized to accept this request'}, status=status.HTTP_403_FORBIDDEN)

        # Create Friendship
        Friendship.objects.create(user1=friend_request.from_user, user2=friend_request.to_user)
        
        # Delete the request
        friend_request.delete()

        return Response({'message': 'Friend request accepted'}, status=status.HTTP_200_OK)

class RejectFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, request_id):
        friend_request = get_object_or_404(FriendRequest, id=request_id)

        if friend_request.to_user != request.user:
            return Response({'error': 'You are not authorized to reject this request'}, status=status.HTTP_403_FORBIDDEN)

        friend_request.delete()
        return Response({'message': 'Friend request rejected'}, status=status.HTTP_200_OK)

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
        serializer = PostSerializer(post, many = True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class PostDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        post = get_object_or_404(Post, id=id, user=request.user)
        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        post = get_object_or_404(Post, id=id, user=request.user)
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
