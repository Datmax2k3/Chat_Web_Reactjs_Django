# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Message, GroupMessage
from .models import Message

User = get_user_model()

class UserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['email', 'first_name', 'last_name', 'id', 'avatar']
        extra_kwargs = {'id': {'read_only': True}}

class MessageSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender_id', 'receiver_id', 'message', 'timestamp', 'file_url']
        extra_kwargs = {'id': {'read_only': True}}

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file_url:
            return request.build_absolute_uri(obj.file_url)
        return None
    
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'avatar']  # or the fields you want to allow the user to update

class GroupMessageSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    sender_avatar = serializers.SerializerMethodField()  # Trả về avatar
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)  # Tùy chọn: trả về tên đầy đủ

    class Meta:
        model = GroupMessage
        fields = ['id', 'group', 'sender_id', 'sender_name', 'message', 'timestamp', 'file_url', 'sender_avatar']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file_url:
            return request.build_absolute_uri(obj.file_url)
        return None

    def get_sender_avatar(self, obj):
        # Trả về URL avatar từ sender
        if obj.sender.avatar:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.sender.avatar.url)
        return None
