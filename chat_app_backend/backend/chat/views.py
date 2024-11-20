# chat/view.py
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from chat.serializers import UserGetSerializer 
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Message, Group, GroupMessage
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import os
from django.core.files.storage import default_storage
from django.conf import settings
from .serializers import UserGetSerializer, UserUpdateSerializer
from rest_framework import status
from django.utils.decorators import method_decorator

User = get_user_model()

@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_user_list(request):
    try:
        user_obj = User.objects.exclude(id=request.user.id)
        serializer = UserGetSerializer(user_obj, many=True)
        return Response(serializer.data, status=200)
    except Exception as e:
        print ("Error in getting user list", str(e))
        return Response({"error": "Error in getting user list"}, status=400)
        
# API lưu tin nhắn mới
@csrf_exempt
def save_message(request):
    if request.method == 'POST':
        sender_id = request.POST.get("senderId")
        receiver_id = request.POST.get("receiverId")
        message_text = request.POST.get("message", "")
        file = request.FILES.get("file")

        if not sender_id or not receiver_id:
            return JsonResponse({"error": "Missing senderId or receiverId"}, status=400)

        # Lấy thông tin người gửi và người nhận
        sender = User.objects.filter(id=sender_id).first()
        receiver = User.objects.filter(id=receiver_id).first()

        if not sender or not receiver:
            return JsonResponse({"error": "Invalid senderId or receiverId"}, status=400)

        # Kiểm tra quyền gửi tin nhắn
        if not sender.is_staff and not sender.is_superuser:
            # Người gửi là người dùng bình thường
            if not receiver.is_staff and not receiver.is_superuser:
                # Người nhận cũng là người dùng bình thường => Chặn
                return JsonResponse({
                    "error": "Normal users cannot send messages to other normal users."
                }, status=403)

        # Lưu file nếu có
        file_url = None
        if file:
            file_path = default_storage.save(os.path.join('uploads', file.name), file)
            file_url = request.build_absolute_uri(settings.MEDIA_URL + file_path)

        # Lưu tin nhắn vào cơ sở dữ liệu
        message = Message.objects.create(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message_text,
            timestamp=timezone.now(),
            file_url=file_url
        )

        return JsonResponse({
            "status": "Message saved",
            "message": message_text,
            "fileUrl": file_url,
            "senderId": sender_id,
            "receiverId": receiver_id,
            "timestamp": message.timestamp
        }, status=201)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@require_http_methods(["GET"])
def get_messages(request):
    user_id = request.GET.get("userId")
    receiver_id = request.GET.get("receiverId")
    group_id = request.GET.get("groupId")

    if not user_id or (not receiver_id and not group_id):
        return JsonResponse({"error": "Missing userId or receiverId/groupId"}, status=400)

    if group_id or (receiver_id and receiver_id.startswith('gr')):  # Kiểm tra nếu receiver_id là nhóm
        # Nếu groupId được truyền, lấy tin nhắn trong nhóm
        messages = GroupMessage.objects.filter(group_id=receiver_id).select_related('sender').order_by('timestamp')
        message_list = [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "message": msg.message,
                "timestamp": msg.timestamp,
                "file_url": msg.file_url,
                "avatar_url": msg.sender.avatar.url if msg.sender.avatar else None,  # Thêm avatar cho nhóm
                "sender_name": msg.sender.last_name if msg.sender.last_name else "Unknown"  # Thêm tên người gửi
            }
            for msg in messages
        ]
    else:
        # Nếu receiver_id được truyền, giữ nguyên cấu trúc dữ liệu khi nhắn tin giữa hai người dùng
        messages = Message.objects.filter(
            (Q(sender_id=user_id) & Q(receiver_id=receiver_id)) |
            (Q(sender_id=receiver_id) & Q(receiver_id=user_id))
        ).order_by('timestamp')

        message_list = list(messages.values("id", "sender_id", "receiver_id", "message", "timestamp", "file_url"))
        
    return JsonResponse(message_list, safe=False)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, id):
    try:
        message = Message.objects.get(id=id)

        # Kiểm tra quyền sở hữu
        if message.sender_id != request.user.id:
            return JsonResponse({"error": "You do not have permission to delete this message."}, status=403)

        message.message = "Tin nhắn đã bị xóa"
        message.file_url = None
        message.save()

        return JsonResponse({"status": "success"}, status=204)
    except Message.DoesNotExist:
        return JsonResponse({"error": "Message not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)
    
def get_user_detail(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        # Serialize and return user data (assuming you're using Django Rest Framework)
        data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            # Add other fields as needed
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
 
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    if request.method == 'GET':
        serializer = UserGetSerializer(user)
        return Response(serializer.data)
    elif request.method == 'PUT':
        data = request.data
        serializer = UserUpdateSerializer(user, data=data, partial=True)

        if serializer.is_valid():
            
            # Kiểm tra và lưu avatar nếu có
            avatar = request.FILES.get('avatar')
            if avatar:
                user.avatar = avatar
                user.save(update_fields=['avatar'])

            # Kiểm tra nếu có thay đổi mật khẩu
            new_password = data.get('new_password')
            if new_password:
                user.set_password(new_password)  # Đặt mật khẩu mới
                user.save(update_fields=['password'])  # Chỉ lưu trường password
            else:
                serializer.save()  # Lưu các trường khác nếu không có mật khẩu mới
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_password(request):
    password = request.data.get('password')
    user = request.user

    # Kiểm tra xem mật khẩu có khớp không
    if user.check_password(password):
        return Response({'valid': True}, status=status.HTTP_200_OK)
    else:
        return Response({'valid': False}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_group(request):
    try:
        group_name = request.data.get("group_name", "").strip()
        members = request.data.get("members", [])

        # Validate group name
        if not group_name:
            return Response({"error": "Group name cannot be empty."}, status=400)

        # Validate members count (at least 3 members including the creator)
        if len(members) < 2:
            return Response({"error": "A group must have at least 3 members (including the creator)."}, status=400)

        # Ensure members are all valid integers
        try:
            members = list(map(int, members))
        except ValueError:
            return Response({"error": "Invalid member ID in the list."}, status=400)

        # Add creator to members list
        creator = request.user
        if creator.id not in members:
            members.append(creator.id)

        # Validate member IDs
        user_objs = User.objects.filter(id__in=members)
        if user_objs.count() != len(set(members)):
            return Response({"error": "One or more members do not exist."}, status=404)

        # Create group
        group = Group.objects.create(name=group_name)
        group.members.set(user_objs)
        group.save()

        return Response({"message": "Group created successfully!", "group_id": group.id}, status=201)
    except Exception as e:
        print(f"Error creating group: {str(e)}")  # Log lỗi
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_groups(request):
    groups = request.user.group_memberships.all()
    return Response({
        "groups": [
            {"id": g.id, "name": g.name, "members_count": g.members.count()}
            for g in groups
        ]
    }, status=200)

@method_decorator(login_required, name='dispatch')
def get_group_messages(request, group_id):
    try:
        messages = GroupMessage.objects.filter(group_id=group_id).order_by('timestamp')
        messages_data = [
            {
                'id': msg.id,
                'message': msg.message,
                'sender_id': msg.sender_id,
                'timestamp': msg.timestamp,
                'file_url': msg.file_url,
                'avatar_url': msg.sender.avatar.url if msg.sender.avatar else None,  # Thêm avatar
            }
            for msg in messages
        ]
        return JsonResponse(messages_data, safe=False)
    except GroupMessage.DoesNotExist:
        return JsonResponse({"error": "Group not found."}, status=404)

@csrf_exempt
def save_group_message(request):
    if request.method == 'POST':
        sender_id = request.user.id
        group_id = request.POST.get("groupId")  # Lấy groupId dạng chuỗi
        message_text = request.POST.get("message", "").strip()
        file = request.FILES.get("file")

        # Kiểm tra dữ liệu
        if not group_id:
            return JsonResponse({"error": "Missing groupId"}, status=400)
        if not message_text and not file:
            return JsonResponse({"error": "Message or file is required"}, status=400)

        # Lưu file (nếu có)
        file_url = None
        if file:
            file_path = default_storage.save(os.path.join('uploads', file.name), file)
            file_url = request.build_absolute_uri(settings.MEDIA_URL + file_path)

        # Lưu tin nhắn vào cơ sở dữ liệu
        try:
            group_message = GroupMessage.objects.create(
                group_id=group_id,
                sender_id=sender_id,
                message=message_text,
                file_url=file_url,
                timestamp=timezone.now(),
            )
        except Exception as e:
            print(f"Error saving group message: {e}")
            return JsonResponse({"error": "Error saving group message"}, status=500)

        return JsonResponse({
            "status": "Group message saved",
            "message": message_text,
            "fileUrl": file_url,
            "senderId": sender_id,
            "groupId": group_id,
            "timestamp": group_message.timestamp,
        }, status=201)
    print(f"Received file: {file}")

    return JsonResponse({"error": "Invalid request method"}, status=405)



@csrf_exempt
def get_group_detail(request, group_id):
    group = Group.objects.filter(id=group_id).first()
    if not group:
        return JsonResponse({"error": "Group not found"}, status=404)

    return JsonResponse({
        "id": group.id,
        "name": group.name,
        "members": list(group.members.values('id', 'username')),
    })

    
    