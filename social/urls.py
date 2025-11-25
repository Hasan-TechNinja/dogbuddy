from django.urls import path
from .views import SendFriendRequestView, AcceptFriendRequestView, RejectFriendRequestView, UnfriendView, FriendListView, PendingRequestsView, PostView, PostDetailView

urlpatterns = [
    path('friend-request/send/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friend-request/accept/<int:request_id>/', AcceptFriendRequestView.as_view(), name='accept-friend-request'),
    path('friend-request/reject/<int:request_id>/', RejectFriendRequestView.as_view(), name='reject-friend-request'),
    path('unfriend/<int:user_id>/', UnfriendView.as_view(), name='unfriend'),
    path('friends/', FriendListView.as_view(), name='friend-list'),
    path('friend-request/pending/', PendingRequestsView.as_view(), name='pending-requests'),
    path('post/', PostView.as_view(), name='post'),
    path('post/update/<int:id>/', PostDetailView.as_view(), name='update-post')
]
