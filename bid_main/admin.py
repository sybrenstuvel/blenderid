from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import ugettext_lazy as _

from . import models

# Configure the admin site. Easier than creating our own AdminSite subclass.
# Text to put at the end of each page's <title>.
admin.site.site_title = 'Blender-ID admin'
# Text to put in each page's <h1>.
admin.site.site_header = 'Blender-ID Administration'


class UserSettingInline(admin.TabularInline):
    model = models.UserSetting
    extra = 0


def make_staff(modeladmin, request, queryset):
    queryset.update(is_staff=True)
make_staff.short_description = 'Make selected users staff'


def unmake_staff(modeladmin, request, queryset):
    queryset.update(is_staff=False)
unmake_staff.short_description = 'Make selected users non-staff'


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    change_form_template = 'loginas/change_form.html'

    inlines = (UserSettingInline, )

    fieldsets = (
        (None, {'fields': ('email', 'password', 'full_name', 'roles')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('date_joined', 'last_update', 'confirmed_email_at')}),
        (_('Login info'), {'fields': ('last_login', 'last_login_ip', 'current_login_ip', 'login_count')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    list_display = ('email', 'full_name', 'is_active', 'is_staff', 'role_names', 'last_update',
                    'confirmed_email_at')
    list_display_links = ('email', 'full_name')
    list_filter = ('roles', 'is_active', 'groups',
                   'confirmed_email_at', 'is_staff', 'is_superuser')
    list_per_page = 12
    search_fields = ('email', 'full_name')
    ordering = ('email', )

    actions = [make_staff, unmake_staff]

    def role_names(self, user):
        """Lists role names of the user.

        Can be used in list_display, but makes things slow.
        """
        roles = user.roles.filter(is_active=True)
        if not roles:
            return '-'
        suffix = ''
        if len(roles) > 3:
            suffix = ', … and %i more…' % (len(roles) - 3)
            roles = roles[:3]
        return ', '.join(g.name for g in roles) + suffix


@admin.register(models.Setting)
class SettingAdmin(admin.ModelAdmin):
    model = models.Setting

    list_display = ('name', 'description', 'data_type', 'default')
    list_filter = ('data_type',)
    search_fields = ('name', 'description')


def make_badge(modeladmin, request, queryset):
    queryset.update(is_badge=True)
make_badge.short_description = 'Mark selected roles as badges'


def make_not_badge(modeladmin, request, queryset):
    queryset.update(is_badge=False)
make_not_badge.short_description = 'Mark selected roles as NOT badges'


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    model = models.Role

    list_display = ('name', 'description', 'is_badge', 'is_active')
    list_filter = ('is_badge', 'is_active')
    search_fields = ('name', 'description')

    actions = [make_badge, make_not_badge]
