from django.urls import path
from .views import SendFriendRequestView, AcceptFriendRequestView, RejectFriendRequestView, UnfriendView, FriendListView, PendingRequestsView, PostView, PostDetailView, LikePostView, CommentView, SharePostView, GeneralUserListView, ProfileView

urlpatterns = [
    path('friend-request/send/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friend-request/accept/<int:request_id>/', AcceptFriendRequestView.as_view(), name='accept-friend-request'),
    path('friend-request/reject/<int:request_id>/', RejectFriendRequestView.as_view(), name='reject-friend-request'),
    path('unfriend/<int:user_id>/', UnfriendView.as_view(), name='unfriend'),
    path('friends/', FriendListView.as_view(), name='friend-list'),
    path('friend-request/pending/', PendingRequestsView.as_view(), name='pending-requests'),
    path('post/', PostView.as_view(), name='post'),
    path('post/update/<int:id>/', PostDetailView.as_view(), name='update-post'),
    path("post/<int:post_id>/like/", LikePostView.as_view(), name='like'),
    path("post/<int:post_id>/comments/", CommentView.as_view(), name='comment'),
    path("post/<int:post_id>/share/", SharePostView.as_view(), name='share'),
    path("users/", GeneralUserListView.as_view(), name="general-user-list"),
    path("profile/<int:user_id>/", ProfileView.as_view(), name="profile-view"),

]
