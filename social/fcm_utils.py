import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import logging

logger = logging.getLogger("django")

# Initialize Firebase only once
_firebase_initialized = False

def initialize_firebase():
    global _firebase_initialized
    if not _firebase_initialized:
        try:
            cred_path = getattr(settings, 'FCM_SERVICE_ACCOUNT_KEY_PATH', None)
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                _firebase_initialized = True
                logger.info("Firebase initialized successfully")
            else:
                logger.warning(f"FCM_SERVICE_ACCOUNT_KEY_PATH not set or file not found at {cred_path}")
        except Exception as e:
            logger.error(f"Error initializing Firebase: {e}")

def send_fcm_notification(user, title, body, data=None):
    """
    Sends a push notification to all devices registered to a specific user.
    """
    initialize_firebase()
    if not _firebase_initialized:
        return None

    from authentication.models import FCMDevice
    devices = FCMDevice.objects.filter(user=user)
    tokens = [device.fcm_token for device in devices]

    if not tokens:
        return None

    # Filter out empty/invalid tokens
    tokens = [t for t in tokens if t]
    if not tokens:
        return None

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        tokens=tokens,
    )

    try:
        response = messaging.send_multicast(message)
        logger.info(f"Successfully sent {response.success_count} messages, {response.failure_count} failures")
        
        # Cleanup invalid tokens if they failed with Unregistered error
        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success and resp.exception and "unregistered" in str(resp.exception).lower():
                    token_to_remove = tokens[idx]
                    FCMDevice.objects.filter(fcm_token=token_to_remove).delete()
                    logger.info(f"Removed unregistered token: {token_to_remove[:20]}...")

        return response
    except Exception as e:
        logger.error(f"Error sending FCM message: {e}")
        return None
