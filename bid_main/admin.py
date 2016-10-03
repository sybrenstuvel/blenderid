from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from . import models


class UserProfileInline(admin.StackedInline):
    model = models.UserProfile
    can_delete = False


class UserSettingInline(admin.StackedInline):
    model = models.UserSetting


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserSettingInline)

    fieldsets = (
        (None, {'fields': ('username', 'password', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    list_display = ('username', 'email', 'get_full_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_full_name(self, user):
        try:
            return user.profile.full_name
        except AttributeError:
            return None

    get_full_name.short_description = 'Full name'


class SettingAdmin(admin.ModelAdmin):
    model = models.Setting

    list_display = ('name', 'description', 'data_type', 'default')
    list_filter = ('data_type',)
    search_fields = ('name', 'description')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(models.Setting, SettingAdmin)
