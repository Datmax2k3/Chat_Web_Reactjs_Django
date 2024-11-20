# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.hashers import make_password
from django.contrib import admin
from chat.models import Group, GroupMessage
from .models import User

# Register the custom User model
@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        # ('Important dates', {'fields': ('last_login',)}),  # Exclude date_joined here
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('password') and not obj.password.startswith('pbkdf2_'):
            obj.set_password(form.cleaned_data['password'])  # Use the built-in method for hashing
        super().save_model(request, obj, form, change)

# Đăng ký UserAdmin đã chỉnh sửa
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
# Đăng ký mô hình Group với Django Admin
admin.site.register(Group)
# Đăng ký mô hình GroupMessage với Django Admin
admin.site.register(GroupMessage)
