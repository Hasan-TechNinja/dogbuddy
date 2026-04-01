import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger("django")

class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user", AnonymousUser())
        
        if not getattr(self.user, "is_authenticated", False):
            logger.info("Rejecting location websocket: unauthenticated")
            await self.close(code=4001)
            return
            
        await self.accept()
        logger.info(f"User {self.user.id} connected for location tracking")

    async def disconnect(self, close_code):
        logger.info(f"User {getattr(self.user, 'id', 'unknown')} disconnected from location tracking")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            
            if latitude is not None and longitude is not None:
                await self._update_location(latitude, longitude)
                await self.send(text_data=json.dumps({
                    "status": "success",
                    "message": "Location updated",
                    "latitude": latitude,
                    "longitude": longitude
                }))
            else:
                await self.send(text_data=json.dumps({
                    "status": "error", 
                    "message": "Latitude and longitude are required"
                }))
        except Exception as exc:
            logger.exception(f"Location receive error: {exc}")
            await self.send(text_data=json.dumps({
                "status": "error",
                "message": "Invalid data format"
            }))

    @database_sync_to_async
    def _update_location(self, lat, lon):
        from authentication.models import Profile
        try:
            profile, created = Profile.objects.get_or_create(user=self.user)
            profile.latitude = lat
            profile.longitude = lon
            profile.save()
        except Exception as e:
            logger.error(f"Error saving location for user {self.user.id}: {e}")
