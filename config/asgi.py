"""
ASGI config for config project with Django Channels support.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing consumers or routes.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter
from config.routing import websocket_application

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": websocket_application,
})
