from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Match /ws/notifications/ with optional trailing slash and query params
    re_path(r'^ws/notifications/?', consumers.TaskConsumer.as_asgi()),
]
