import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model

from .models import ChatMessage
from .serializers import ChatMessageSerializer

User = get_user_model()
logger = logging.getLogger("django")



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = None
        self.room_group_name = None

        try:
            self.user = self.scope.get("user", AnonymousUser())
            logger.info(f"WS connect: user={self.user} auth={getattr(self.user, 'is_authenticated', False)}")

            # enforce authenticated users
            if not getattr(self.user, "is_authenticated", False):
                logger.info("Rejecting websocket connection: unauthenticated")
                await self.close(code=4001)
                return

            try:
                self.other_user_id = int(self.scope["url_route"]["kwargs"]["user_id"])
            except Exception:
                logger.error("connect: invalid or missing user_id")
                await self.close(code=4002)
                return

            other = await self._get_user(self.other_user_id)
            if not other:
                logger.error(f"connect: other user {self.other_user_id} not found")
                await self.close(code=4004)
                return

            # CONSISTENT ROOM NAME for both users
            a = int(getattr(self.user, "id", 0) or 0)
            b = int(self.other_user_id)
            low, high = sorted((a, b))

            self.room_name = f"chat_{low}_{high}"
            self.room_group_name = self.room_name

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            logger.info(f"User {getattr(self.user, 'id', None)} connected to room {self.room_group_name}")

            # send recent history (most recent first reversed to chronological)
            last_messages = await self._get_last_messages(user_a_id=a, user_b_id=b, limit=20)
            serialized = [await self._serialize(m) for m in reversed(last_messages)]
            await self.send(text_data=json.dumps({"history": serialized}))

        except Exception as exc:
            logger.exception(f"Error in connect: {exc}")
            try:
                await self.close(code=500)
            except Exception:
                pass


    async def disconnect(self, close_code):
        try:
            if self.room_group_name:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
            logger.info(f"User {getattr(self.user, 'id', None)} disconnected from {self.room_group_name}")
        except Exception as exc:
            logger.exception(f"disconnect error: {exc}")

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if not text_data:
                await self.send(text_data=json.dumps({"error": "Empty message"}))
                return

            data = json.loads(text_data)
            message = data.get("message")

            if not message or not isinstance(message, str):
                await self.send(text_data=json.dumps({"error": "Message required"}))
                return

            # Create message in DB
            chat_msg = await self._create_message(
                sender_id=self.user.id,
                receiver_id=self.other_user_id,
                message=message
            )

            serialized = await self._serialize(chat_msg)

            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": serialized
                }
            )
        except Exception as exc:
            logger.exception(f"receive error: {exc}")
            await self.send(text_data=json.dumps({"error": "Invalid message format"}))

    async def chat_message(self, event):
        try:
            await self.send(text_data=json.dumps(event["message"]))
        except Exception as exc:
            logger.exception(f"chat_message error: {exc}")

    # DB METHODS
    @database_sync_to_async
    def _get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def _create_message(self, sender_id, receiver_id, message):
        return ChatMessage.objects.create(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message
        )

    @database_sync_to_async
    def _serialize(self, chat_message):
        return ChatMessageSerializer(chat_message).data

    @database_sync_to_async
    def _get_last_messages(self, user_a_id, user_b_id, limit=20):
        return list(
            ChatMessage.objects.filter(
                sender_id__in=[user_a_id, user_b_id],
                receiver_id__in=[user_a_id, user_b_id]
            ).order_by("-timestamp")[:limit]
        )
