from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class UserAdmin(UserAdmin):
    search_fields = ('email', 'username', 'first_name')
    ordering = ('-date_joined',)
    list_display = ('email', 'username', 'first_name', 'is_active', 'is_staff')
    list_editable = ('is_active',)
    list_filter = ('email', 'first_name', 'is_active',
                   'is_staff')
    fieldsets = [
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superuser')}),
    ]
