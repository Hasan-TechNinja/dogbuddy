import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatGroup, GroupMember, GroupMessage
from .serializers import GroupMessageSerializer

User = get_user_model()
logger = logging.getLogger("django")


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope.get("user")
            if not self.user or not self.user.is_authenticated:
                await self.close(code=4001)
                return

            self.group_id = int(self.scope["url_route"]["kwargs"]["group_id"])

            group = await self._get_group(self.group_id)
            if not group:
                await self.close(code=4004)
                return

            # MUST be a member
            if not await self._is_member(self.user.id, self.group_id):
                await self.close(code=4003)  # forbidden
                return

            self.room_group_name = f"group_{self.group_id}"

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

            # send last 30 messages
            messages = await self._get_last_messages()
            serialized = [await self._serialize(m) for m in messages]
            await self.send(json.dumps({"history": serialized}))

        except Exception as e:
            logger.exception("group connect error")
            await self.close(code=500)

    async def disconnect(self, code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if not text_data:
                return

            data = json.loads(text_data)
            message = data.get("message")
            if not message:
                return

            msg_obj = await self._create_message(self.user.id, self.group_id, message)
            serialized = await self._serialize(msg_obj)

            # broadcast to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "group_message", "message": serialized}
            )

        except Exception as e:
            logger.exception("group receive error")

    async def group_message(self, event):
        await self.send(json.dumps(event["message"]))

    # ---------------- DB METHODS ----------------

    @database_sync_to_async
    def _get_group(self, group_id):
        try:
            return ChatGroup.objects.get(id=group_id)
        except ChatGroup.DoesNotExist:
            return None

    @database_sync_to_async
    def _is_member(self, user_id, group_id):
        return GroupMember.objects.filter(user_id=user_id, group_id=group_id).exists()

    @database_sync_to_async
    def _get_last_messages(self, limit=30):
        return list(
            GroupMessage.objects.filter(group_id=self.group_id)
            .order_by("-timestamp")[:limit]
        )[::-1]

    @database_sync_to_async
    def _create_message(self, user_id, group_id, message):
        return GroupMessage.objects.create(
            sender_id=user_id,
            group_id=group_id,
            message=message
        )

    @database_sync_to_async
    def _serialize(self, msg):
        # Extract host from headers to build absolute URLs
        headers = dict(self.scope.get('headers', []))
        host = headers.get(b'host', b'').decode()
        base_url = f"http://{host}" if host else ""
        return GroupMessageSerializer(msg, context={'base_url': base_url}).data
