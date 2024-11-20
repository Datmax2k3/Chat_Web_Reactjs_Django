# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from accounts.views import register_user, login, verify_email, current_user_view
from chat.views import get_user_list, create_group, get_user_groups
from django.conf import settings
from django.conf.urls.static import static
from chat.views import user_profile

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', register_user, name="register"),
    path('verify-email/', verify_email, name="verify_email"),
    path('login/', login, name="login"),
    path('api/users/',get_user_list, name="users"),
    path('', include('chat.urls')),
    path('api/profile/', user_profile, name='user_profile'),
    path('api/users/me/', current_user_view, name='current_user'),
    path('api/groups/user/', get_user_groups, name='user-groups')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)   
