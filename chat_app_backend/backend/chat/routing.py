# routing.py
from django.urls import path, re_path
from .consumers import PersonalChatConsumer, GroupChatConsumer
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:id>/', PersonalChatConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<user_id>\d+)/(?P<receiver_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/group_chat/(?P<group_id>[a-zA-Z0-9]+)/$', GroupChatConsumer.as_asgi()),  # Đảm bảo group_id có thể là string
]