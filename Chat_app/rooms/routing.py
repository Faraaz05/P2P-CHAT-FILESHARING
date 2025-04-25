# urls route for websocket connection
# Using re_path instead of path because it allows the use of regular expressions for URL patterns
from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
]