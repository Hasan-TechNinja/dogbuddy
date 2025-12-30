from django.urls import path
from .views import ChatMessageView, SendFriendRequestView, AcceptFriendRequestView, RejectFriendRequestView, CancelFriendRequestView, UnfriendView, FriendListView, PendingRequestsView, PostView, PostDetailView, LikePostView, CommentView, SharePostView, GeneralUserListView, ProfileView, CreateGroup, JoinGroup, UserFriendStatusListView
from . import views

urlpatterns = [
    path('friend-request/send/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friend-request/accept/<int:user_id>/', AcceptFriendRequestView.as_view(), name='accept-friend-request'),
    path('friend-request/reject/<int:user_id>/', RejectFriendRequestView.as_view(), name='reject-friend-request'),
    path('friend-request/cancel/<int:user_id>/', CancelFriendRequestView.as_view(), name='cancel-friend-request'),
    path('unfriend/<int:user_id>/', UnfriendView.as_view(), name='unfriend'),
    path('friends/', FriendListView.as_view(), name='friend-list'),
    path('friend-request/pending/', PendingRequestsView.as_view(), name='pending-requests'),
    path('post/', PostView.as_view(), name='post'),
    path('post/update/<int:id>/', PostDetailView.as_view(), name='update-post'),
    path("post/<int:post_id>/like/", LikePostView.as_view(), name='like'),
    path("post/<int:post_id>/comments/", CommentView.as_view(), name='comment'),
    path("post/<int:post_id>/share/", SharePostView.as_view(), name='share'),
    path("users/", GeneralUserListView.as_view(), name="general-user-list"),
    path("users/friend-status/", UserFriendStatusListView.as_view(), name="user-friend-status-list"),
    path("profile/<int:user_id>/", ProfileView.as_view(), name="profile-view"),
    path('chat/messages/<int:chat_partner_id>/', ChatMessageView.as_view(), name='chat-messages'),
    path('create-group/', CreateGroup.as_view(), name='create-group'),
    path('group/<int:group_id>/add-member/', JoinGroup.as_view(), name='add-group-member'),
    path('group/members/<int:group_id>/', views.GroupMembers.as_view(), name='group-members'),
    path('group/<int:group_id>/remove-member/', views.RemoveGroupMemberView.as_view(), name='remove-group-member')

]
