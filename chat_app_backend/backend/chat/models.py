# chat/models.py
from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_save

class Message(models.Model):
    id = models.AutoField(primary_key=True)
    sender_id = models.IntegerField()  # Chuyển sang IntegerField nếu user ID là số
    receiver_id = models.IntegerField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    file_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Message from {self.sender_id} to {self.receiver_id} at {self.timestamp}"
    
class Group(models.Model):
    id = models.CharField(max_length=50, primary_key=True, unique=True, editable=False)  # Sử dụng CharField
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='group_memberships')

    def __str__(self):
        return f"Group: {self.name} (ID: {self.id})"

@receiver(pre_save, sender=Group)
def set_group_id(sender, instance, **kwargs):
    if not instance.id:  # Chỉ tạo ID nếu chưa có
        last_group = Group.objects.order_by('-created_at').first()
        next_id = 1 if not last_group else int(last_group.id[2:]) + 1  # Lấy phần số trong ID cuối cùng
        instance.id = f"gr{next_id}"  # Gán ID mới
    
class GroupMessage(models.Model):
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    file_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Message in Group {self.group.id} from {self.sender_id} at {self.timestamp}"
