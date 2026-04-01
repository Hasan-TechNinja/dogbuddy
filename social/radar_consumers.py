import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q

logger = logging.getLogger("django")

class RadarConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user", AnonymousUser())
        
        if not getattr(self.user, "is_authenticated", False):
            logger.info("Radar: Rejecting unauthenticated connection")
            await self.close(code=4001)
            return
            
        await self.accept()
        logger.info(f"Radar: User {self.user.id} ({self.user.username}) connected")

    async def disconnect(self, close_code):
        logger.info(f"Radar: User {getattr(self.user, 'id', 'unknown')} disconnected (code: {close_code})")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            radius_km = data.get("radius", 1.0)
            
            # Cast radius to float safely
            try:
                radius_km = float(radius_km)
            except (TypeError, ValueError):
                radius_km = 1.0

            # Get nearby users using location from profile
            radar_response = await self._get_radar_data(radius_km)
            
            if isinstance(radar_response, dict) and "error" in radar_response:
                await self.send(text_data=json.dumps(radar_response))
            else:
                await self.send(text_data=json.dumps({
                    "type": "radar_update",
                    "radius": radius_km,
                    "users": radar_response
                }))

        except Exception as exc:
            logger.exception(f"Radar: receive error: {exc}")
            await self.send(text_data=json.dumps({"error": "Processing error on server"}))

    @database_sync_to_async
    def _get_radar_data(self, radius_km):
        from authentication.models import Profile
        from pet.models import PetInfo
        from social.models import Friendship
        from social.utils import get_distance_between_points

        # 1. Get my current location from profile
        try:
            profile_obj, created = Profile.objects.get_or_create(user=self.user)
            if profile_obj.latitude is None or profile_obj.longitude is None:
                return {"error": "Your location is not set. Use ws/location/ first."}
            
            my_lat = float(profile_obj.latitude)
            my_lon = float(profile_obj.longitude)
        except Exception as e:
            logger.error(f"Radar: Profile error for user {self.user.id}: {e}")
            return {"error": "Could not access profile location."}

        # 2. Get my friends
        friendships = Friendship.objects.filter(Q(user1=self.user) | Q(user2=self.user))
        friend_ids = set()
        for f in friendships:
            friend_ids.add(f.user1_id if f.user2_id == self.user.id else f.user2_id)

        # 3. Get all other profiles with location (exclude self)
        other_profiles = Profile.objects.exclude(user=self.user).exclude(
            latitude__isnull=True, longitude__isnull=True
        )

        results = []
        for other in other_profiles:
            try:
                dist = get_distance_between_points(
                    my_lat, my_lon, 
                    float(other.latitude), float(other.longitude)
                )
                
                if dist is not None and dist <= radius_km:
                    
                    # 4. Check pet status (exclude snooze)
                    active_pets = PetInfo.objects.filter(owner=other.user).exclude(status='snooze')
                    if not active_pets.exists():
                        continue 

                    # Decide dominant status
                    if active_pets.filter(status='playing').exists():
                        top_status = 'playing'
                    else:
                        top_status = 'walking'

                    # 5. Color Logic
                    is_buddy = other.user_id in friend_ids
                    if is_buddy:
                        color = "pink" if top_status == 'playing' else "green"
                    else:
                        color = "blue"

                    results.append({
                        "id": other.user.id,
                        "username": other.user.username,
                        "name": other.name,
                        "image": other.profile_image.url if other.profile_image else None,
                        "latitude": float(other.latitude),
                        "longitude": float(other.longitude),
                        "distance_km": dist,
                        "color": color,
                        "status": top_status
                    })
            except Exception as e:
                logger.warning(f"Radar: Skipping user {other.user_id} due to error: {e}")
                continue
        
        results.sort(key=lambda x: x['distance_km'])
        return results
