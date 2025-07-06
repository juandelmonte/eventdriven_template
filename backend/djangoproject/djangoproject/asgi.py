import os
import django
import sys
import logging

print("===== ASGI MODULE LOADING =====")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoproject.settings')
django.setup()  # Set up Django before importing models

print("===== DJANGO SETUP COMPLETE =====")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator

from tasks.routing import websocket_urlpatterns
from tasks.middleware import JWTAuthMiddleware
from tasks.consumers import TaskConsumer

print("===== ASGI IMPORTS COMPLETE =====")
print(f"WebSocket URL patterns: {websocket_urlpatterns}")

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

# Debug Origin Validator
class DebugOriginValidator:
    def __init__(self, application):
        self.application = application
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            headers = dict(scope.get("headers", []))
            origin = headers.get(b"origin", b"").decode()
            host = headers.get(b"host", b"").decode()
            print(f"===== WEBSOCKET CONNECTION =====")
            print(f"Origin: {origin}")
            print(f"Host: {host}")
            print(f"Path: {scope.get('path')}")
            print(f"Query String: {scope.get('query_string')}")
            sys.stdout.flush()
        
        return await self.application(scope, receive, send)

# Application definition - BYPASSING AllowedHostsOriginValidator for testing
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": DebugOriginValidator(  # Add debugging
        # Remove AllowedHostsOriginValidator temporarily
        JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

print("===== ASGI APPLICATION CONFIGURED =====")
sys.stdout.flush()