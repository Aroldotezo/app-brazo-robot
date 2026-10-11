from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import detecciones.routing

# Root WebSocket application router for the project
websocket_application = AuthMiddlewareStack(
    URLRouter(
        detecciones.routing.websocket_urlpatterns
    )
)
