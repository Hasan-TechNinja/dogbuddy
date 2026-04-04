from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q, Max, OuterRef, Subquery, Count, F
from .models import ChatGroup, ChatMessage, FriendRequest, Friendship, GroupMember, Post, Comment, Share
from .serializers import ChatMessageSerializer, FriendRequestSerializer, FriendshipSerializer, PostSerializer, CommentSerializer, ShareSerializer, UserFriendStatusSerializer, ChatUserListSerializer, ChatGroupListSerializer, GroupMessageSerializer
from authentication.serializers import ProfileSerializer, UserSerializer
from authentication.models import Profile
from rest_framework.pagination import PageNumberPagination
from .utils import get_distance_between_points
from pet.models import PetInfo
from .fcm_utils import send_fcm_notification

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserDistanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)
        
        my_profile = getattr(request.user, 'profile', None)
        target_profile = getattr(target_user, 'profile', None)
        
        if not my_profile or not target_profile:
            return Response({"error": "Profile not found"}, status=404)
            
        distance = get_distance_between_points(
            my_profile.latitude, my_profile.longitude,
            target_profile.latitude, target_profile.longitude
        )
        
        if distance is None:
            return Response({"error": "Location not set for one or both users"}, status=400)
            
        return Response({
            "target_user_id": user_id,
            "target_username": target_user.username,
            "name": target_profile.name,
            "image": request.build_absolute_uri(target_profile.profile_image.url) if target_profile.profile_image else None,
            "distance_km": distance
        })

class NearbyUsersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        radius_km = request.query_params.get('radius', 1)  # Default 1 km
        try:
            radius_km = float(radius_km)
        except ValueError:
            return Response({"error": "Invalid radius"}, status=400)

        # Filtering parameters
        filter_query = request.query_params.get('filter', '')
        filter_list = [f.strip().lower() for f in filter_query.split(',')] if filter_query else []

        my_profile = getattr(request.user, 'profile', None)
        if not my_profile or my_profile.latitude is None or my_profile.longitude is None:
            return Response({"error": "Current user location not set"}, status=400)

        my_lat = float(my_profile.latitude)
        my_lon = float(my_profile.longitude)

        # Identify buddy IDs for the current user
        friendships = Friendship.objects.filter(Q(user1=request.user) | Q(user2=request.user))
        buddy_ids = set()
        for f in friendships:
            buddy_ids.add(f.user1_id if f.user2_id == request.user.id else f.user2_id)

        # Basic filtering: Get profiles with location set
        other_profiles = Profile.objects.exclude(user=request.user).exclude(
            latitude__isnull=True, longitude__isnull=True
        ).select_related('user')

        nearby_users = []
        for profile in other_profiles:
            dist = get_distance_between_points(
                my_lat, my_lon, 
                float(profile.latitude), float(profile.longitude)
            )
            
            if dist is not None and dist <= radius_km:
                user_id = profile.user.id
                is_buddy = user_id in buddy_ids
                
                # Fetch detailed pet info for this user
                user_pets = PetInfo.objects.filter(owner_id=user_id)
                pet_details = []
                pet_statuses = []
                for p in user_pets:
                    pet_statuses.append(p.status)
                    pet_details.append({
                        "name": p.name,
                        "status": p.status,
                        "gender": p.gender,
                        "size": p.size,
                        "life_stage": p.life_stage # Property from PetInfo model
                    })
                
                # Apply categorization filters
                if filter_list:
                    keep = False
                    if 'buddies' in filter_list and is_buddy:
                        keep = True
                    if ('general' in filter_list or 'general_user' in filter_list or 'general user' in filter_list) and not is_buddy:
                        keep = True
                    if 'playing' in filter_list and 'playing' in pet_statuses:
                        keep = True
                    if ('walk' in filter_list or 'walking' in filter_list) and 'walking' in pet_statuses:
                        keep = True
                    
                    if not keep:
                        continue

                nearby_users.append({
                    "id": user_id,
                    "username": profile.user.username,
                    "name": profile.name,
                    "image": request.build_absolute_uri(profile.profile_image.url) if profile.profile_image else None,
                    "distance_km": dist,
                    "latitude": float(profile.latitude),
                    "longitude": float(profile.longitude),
                    "is_buddy": is_buddy,
                    "pets": pet_details
                })

        # Sort by distance
        nearby_users.sort(key=lambda x: x['distance_km'])

        return Response({
            "count": len(nearby_users),
            "radius_km": radius_km,
            "nearby_users": nearby_users
        })

class InviteNearbyUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        to_user_ids = request.data.get('to_user_ids')
        
        if not to_user_ids or not isinstance(to_user_ids, list):
            return Response({'error': 'to_user_ids must be a list of user IDs'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Content remains fixed for "Come to play" as requested
        title = "Play Invite"
        body = f"{request.user.profile.name or request.user.username} would like to play with you and your dog!"
        
        sent_to = []
        for user_id in to_user_ids:
            try:
                to_user = User.objects.get(id=user_id)
                if request.user == to_user:
                    continue # Cannot invite self
                
                send_fcm_notification(
                    user=to_user,
                    title=title,
                    body=body,
                    data={
                        "type": "proximity_invite", 
                        "from_user_id": str(request.user.id),
                        "invite_type": "play"
                    }
                )
                sent_to.append(user_id)
            except User.DoesNotExist:
                continue

        return Response({
            'message': f'Invitation sent to {len(sent_to)} user(s)',
            'sent_to_ids': sent_to
        }, status=status.HTTP_200_OK)


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
        
        # Trigger FCM Notification
        send_fcm_notification(
            user=to_user,
            title="New Friend Request",
            body=f"{request.user.profile.name or request.user.username} sent you a friend request!",
            data={"type": "friend_request", "from_user_id": str(request.user.id)}
        )
        
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    
class AcceptFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        friend_request = get_object_or_404(FriendRequest, from_user__id=user_id, to_user=request.user)

        # Create Friendship
        Friendship.objects.create(user1=friend_request.from_user, user2=friend_request.to_user)
        
        # Trigger FCM Notification
        send_fcm_notification(
            user=friend_request.from_user,
            title="Friend Request Accepted",
            body=f"{request.user.profile.name or request.user.username} accepted your friend request!",
            data={"type": "friend_request_accepted", "from_user_id": str(request.user.id)}
        )
        
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
        search_query = request.query_params.get('search', '')
        
        friendships = Friendship.objects.filter(Q(user1=request.user) | Q(user2=request.user))
        friend_ids = []
        for friendship in friendships:
            if friendship.user1 == request.user:
                friend_ids.append(friendship.user2_id)
            else:
                friend_ids.append(friendship.user1_id)
        
        profiles = Profile.objects.filter(user_id__in=friend_ids)
        
        if search_query:
            profiles = profiles.filter(
                Q(name__icontains=search_query) | 
                Q(user__username__icontains=search_query)
            )
            
        serializer = UserFriendStatusSerializer(profiles, many=True, context={'request': request})
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
        serializer = ChatMessageSerializer(messages, many=True, context={'request': request})
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
        memberships = GroupMember.objects.filter(user=request.user).select_related("group").order_by('-group__created_at')
        groups = [m.group for m in memberships]
        
        paginator = StandardResultsSetPagination()
        paginated_groups = paginator.paginate_queryset(groups, request)
        
        serializer = ChatGroupListSerializer(paginated_groups, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    

class MyChatUsersListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get latest message time and text for each conversation partner
        last_msg_subquery = ChatMessage.objects.filter(
            Q(sender=user, receiver=OuterRef('user_id')) |
            Q(sender=OuterRef('user_id'), receiver=user)
        ).order_by('-timestamp')

        last_time = Subquery(last_msg_subquery.values('timestamp')[:1])
        last_text = Subquery(last_msg_subquery.values('message')[:1])

        # Fetch users who are friends
        friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        friend_ids = list(friendships.values_list('user1_id', flat=True)) + list(friendships.values_list('user2_id', flat=True))
        
        # Fetch users who have had a chat with the current user
        chat_partners_ids = list(User.objects.filter(
            Q(sent_messages__receiver=user) | Q(received_messages__sender=user)
        ).exclude(id=user.id).values_list('id', flat=True).distinct())

        # Combine IDs and exclude self
        all_user_ids = list(set(friend_ids + chat_partners_ids))
        if user.id in all_user_ids:
            all_user_ids.remove(user.id)

        # Map to profiles and annotate with details
        profiles = Profile.objects.filter(user_id__in=all_user_ids).annotate(
            last_message_time=last_time,
            last_message_text=last_text,
            unseen_cnt=Count(
                'user__sent_messages', 
                filter=Q(user__sent_messages__receiver=user, user__sent_messages__is_read=False)
            )
        ).order_by('-last_message_time')

        paginator = StandardResultsSetPagination()
        paginated_profiles = paginator.paginate_queryset(profiles, request)

        # Add the dynamic attribute for the serializer to avoid O(N) queries
        for profile in paginated_profiles:
            setattr(profile, f'unseen_count_{user.id}', profile.unseen_cnt)

        serializer = ChatUserListSerializer(
            paginated_profiles,
            many=True,
            context={"request": request}
        )

        return paginator.get_paginated_response(serializer.data)


class GroupChatMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        group = get_object_or_404(ChatGroup, id=group_id)
        
        # Check if the user is a member of the group
        is_member = GroupMember.objects.filter(group=group, user=request.user).exists()
        if not is_member:
            return Response({"error": "You are not a member of this group"}, status=status.HTTP_403_FORBIDDEN)
            
        messages = group.messages.all().order_by('timestamp')
        serializer = GroupMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)