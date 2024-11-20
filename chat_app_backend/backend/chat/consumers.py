# consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Message, GroupMessage, Group
from channels.db import database_sync_to_async


# Hàm lưu tin nhắn vào database
@database_sync_to_async
def save_message(sender_id, receiver_id, message, file_url=None):  # Thêm tham số `file_url`
    Message.objects.create(sender_id=sender_id, receiver_id=receiver_id, message=message, file_url=file_url)

class PersonalChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        request_user = self.scope['user']
        if request_user.is_authenticated:
            chat_with_user = self.scope['url_route']['kwargs']['id']
            user_ids = sorted([int(request_user.id), int(chat_with_user)])
            self.room_group_name = f"chat_{user_ids[0]}-{user_ids[1]}"
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

    async def receive(self, text_data=None, **kwargs):
        data = json.loads(text_data)
        message = data['message']
        sender_id = self.scope['user'].id
        receiver_id = data.get('receiverId')
        file_url = data.get('fileUrl')

        # Save message to database
        await save_message(sender_id, receiver_id, message, file_url)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "senderId": sender_id,
                "receiverId": receiver_id,
                "fileUrl": file_url,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event['message'],
            "senderId": event['senderId'],
            "receiverId": event['receiverId'],
            "fileUrl": event.get('fileUrl')
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']
        
        # Tạo tên group bằng cách kết hợp `user_id` và `receiver_id` theo một trật tự nhất định
        self.room_group_name = f"chat_{min(self.user_id, self.receiver_id)}_{max(self.user_id, self.receiver_id)}"

        # Thêm vào group để gửi tin nhắn
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Rời khỏi group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_id = data['senderId']
        receiver_id = data['receiverId']

        # Phát tin nhắn đến group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'senderId': sender_id,
                'receiverId': receiver_id
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_id = event['senderId']
        receiver_id = event['receiverId']
        file_url = event.get('fileUrl')  # Use .get to handle optional fileUrl

        # Send the message to WebSocket client
        await self.send(text_data=json.dumps({
            'message': message,
            'senderId': sender_id,
            'receiverId': receiver_id,
            'fileUrl': file_url  # Include fileUrl in the response to client
        }))
        
@database_sync_to_async
def save_group_message(group_id, sender_id, message, file_url=None):
    group = Group.objects.filter(id=group_id).first()
    if group:
        GroupMessage.objects.create(
            group=group,
            sender_id=sender_id,
            message=message,
            file_url=file_url
        )

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.group_name = f"group_{self.group_id}"

        if self.scope['user'].is_authenticated:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')
        file_url = text_data_json.get('fileUrl')  # Lấy fileUrl từ dữ liệu nhận
        sender_id = self.scope['user'].id

        # Lấy thông tin avatar của người gửi
        user = self.scope['user']
        avatar_url = user.avatar.url if user.avatar else None  # Nếu `avatar` là một trường ImageField

        # Lưu tin nhắn vào cơ sở dữ liệu
        await save_group_message(self.group_id, sender_id, message, file_url)

        # Gửi tin nhắn đến tất cả các client trong group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': message,
                'senderId': sender_id,
                'fileUrl': file_url,  # Đảm bảo rằng fileUrl được gửi
                'avatarUrl': avatar_url,  # Thêm avatarUrl vào sự kiện
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_id = event['senderId']
        file_url = event.get('fileUrl')  # Lấy fileUrl từ sự kiện gửi tới
        avatar_url = event.get('avatarUrl')  # Lấy avatarUrl từ sự kiện gửi tới

        # Gửi tin nhắn đến WebSocket client
        await self.send(text_data=json.dumps({
            'message': message,
            'senderId': sender_id,
            'fileUrl': file_url,  # Đảm bảo fileUrl được gửi cùng tin nhắn
            'avatarUrl': avatar_url,  # Gửi avatarUrl
        }))
