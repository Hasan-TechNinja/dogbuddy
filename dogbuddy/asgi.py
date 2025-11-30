"""
ASGI config for dogbuddy project.
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dogbuddy.settings")

# 🔥 Load Django BEFORE importing anything from Django apps
django.setup()

# Only import AFTER settings + Django setup is completed
from social.routing import websocket_urlpatterns
from social.middleware import JWTAuthMiddleware

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    # 🔥 Use custom JWT middleware for WebSocket authentication
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
