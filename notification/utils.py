import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import logging
from .models import FCMDevice, Notification

logger = logging.getLogger("django")

_firebase_initialized = False

def initialize_firebase():
    global _firebase_initialized
    if not _firebase_initialized:
        try:
            cred_dict = getattr(settings, 'FCM_CREDENTIALS_DICT', None)
            cred_path = getattr(settings, 'FCM_SERVICE_ACCOUNT_KEY_PATH', None)
            
            cred = None
            if cred_dict:
                cred = credentials.Certificate(cred_dict)
            elif cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                
            if cred:
                # Check if app already initialized
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
                _firebase_initialized = True
                logger.info("Firebase initialized successfully")
            else:
                logger.warning("Firebase credentials not found (neither dict nor file)")
        except Exception as e:
            logger.error(f"Error initializing Firebase: {e}")

def send_push_notification(user, title, body, data=None, save_to_db=True):
    """
    Sends a push notification to all devices registered to a specific user.
    """
    initialize_firebase()
    
    # Save to db
    if save_to_db:
        Notification.objects.create(
            user=user,
            title=title,
            body=body,
            notification_type=data.get('type') if data else '',
            data=data or {}
        )

    if not _firebase_initialized:
        return None

    devices = FCMDevice.objects.filter(user=user)
    tokens = [device.fcm_token for device in devices if device.fcm_token]

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
