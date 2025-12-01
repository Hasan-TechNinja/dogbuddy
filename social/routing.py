from django.urls import path
from . import consumers
from . consumers_group import GroupChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<int:user_id>/", consumers.ChatConsumer.as_asgi()),
    path("ws/group/<int:group_id>/", GroupChatConsumer.as_asgi()),
]