# chat/urls.py
from django.urls import path
from . import views
from .views import save_message, get_user_groups, create_group, get_group_detail
from django.conf.urls.static import static
from .views import delete_message
from django.conf import settings
from chat.views import user_profile

urlpatterns = [
    path('api/messages', views.get_messages, name='get_messages'),
    path('api/messages/save', views.save_message, name='save_message'),
    path('api/messages/delete/<int:id>/', views.delete_message, name='delete_message'),
    path('api/users/<int:user_id>/', views.get_user_detail, name='get_user_detail'),
    path('api/profile/', views.user_profile, name='user_profile'),
    path('api/verify-password/', views.verify_password, name='verify_password'),
    path('api/groups/', create_group, name='create_group'),
    # path('api/groups/<str:group_id>/', get_group_detail, name='get_group_detail'),
    path('api/group_messages/save', views.save_group_message, name='save_group_message'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)