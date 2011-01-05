import os
import sys

__all__ = ('NEWSROOM_MEDIA_URL', 'NEWSROOM_MEDIA_ROOT', 'LOCAL_DEV_SERVER')

APP_ROOT = os.path.dirname(os.path.dirname(os.path.normpath(__file__)))

NEWSROOM_MEDIA_URL = '/newsroom-media/'
NEWSROOM_MEDIA_ROOT = os.path.join(APP_ROOT, 'media')

LOCAL_DEV_SERVER = 'manage.py' in sys.argv
