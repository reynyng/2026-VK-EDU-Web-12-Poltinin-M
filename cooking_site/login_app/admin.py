from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'get_nickname', 'is_staff')
    
    def get_nickname(self, instance):
        return instance.profile.nickname if hasattr(instance, 'profile') else '-'
    get_nickname.short_description = 'Никнейм'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)