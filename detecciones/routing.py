from django.urls import re_path
from . import consumers

# WebSocket URL patterns for the camera streaming consumer
websocket_urlpatterns = [
    re_path(r'^ws/camera/(?P<camera_id>[\w\-]+)/?$', consumers.CameraStreamConsumer.as_asgi()),
    re_path(r'^ws/camera/?$', consumers.CameraStreamConsumer.as_asgi()),
]
