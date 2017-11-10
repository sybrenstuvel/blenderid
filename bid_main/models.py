from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import oauth2_provider.models as oa2_models


class UserManager(BaseUserManager):
    """UserManager that doesn't use a username, but an email instead."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    User class for BlenderID, implementing a fully featured User model with
    admin-compliant permissions.

    Email and password are required. Other fields are optional.
    """

    email = models.EmailField(
        _('email address'),
        max_length=64,
        unique=True,
        help_text=_('Required. 64 characters or fewer.'),
        error_messages={
            'unique': _("A user with that email address already exists."),
        },
    )
    full_name = models.CharField(_('full name'), max_length=80, blank=True)
    roles = models.ManyToManyField('Role', related_name='users', blank=True)

    confirmed_email_at = models.DateTimeField(
        null=True, blank=True,
        help_text=_('Designates the date & time at which the user confirmed their email address. '
                    'None if not yet confirmed.'))
    last_login_ip = models.GenericIPAddressField(
        null=True, blank=True,
        help_text=_('IP address (IPv4 or IPv6) used for previous login, if any.'))
    current_login_ip = models.GenericIPAddressField(
        null=True, blank=True,
        help_text=_('IP address (IPv4 or IPv6) used for current login, if any.'))
    login_count = models.PositiveIntegerField(
        default=0, blank=True,
        help_text=_('Number of times this user logged in.'))

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_update = models.DateTimeField(_('last update'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def save(self, *args, **kwargs):
        self.last_update = timezone.now()

        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'].append('last_update')
        return super().save(*args, **kwargs)

    def get_full_name(self):
        """
        Returns the full name.
        """
        return self.full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        parts = self.full_name.split(' ', 1)
        return parts[0]

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def has_confirmed_email(self):
        return self.confirmed_email_at is not None

    @property
    def role_names(self):
        return {role.name for role in self.roles.all()}


class SettingValueField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 128
        super().__init__(*args, **kwargs)


SETTING_DATA_TYPE_CHOICES = [
    ('bool', 'Boolean'),
]


class Setting(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=128)
    data_type = models.CharField(max_length=32, choices=SETTING_DATA_TYPE_CHOICES, default='bool')
    default = SettingValueField()
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='UserSetting')

    def __str__(self):
        return self.name.replace('_', ' ').title()


class UserSetting(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    setting = models.ForeignKey(Setting, on_delete=models.CASCADE)
    unconstrained_value = SettingValueField()

    def __str__(self):
        return 'Setting %r of %r' % (self.setting.name, self.user.email)


class Role(models.Model):
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=255, blank=True, null=False)
    is_active = models.BooleanField(default=True, null=False)
    is_badge = models.BooleanField(default=False, null=False)
    is_public = models.BooleanField(default=True, null=False)

    may_manage_roles = models.ManyToManyField(
        'Role', related_name='managers', blank=True,
        help_text='Users with this role will be able to grant or revoke these roles to any other user.')

    class Meta:
        ordering = ['-is_active', 'name']

    def __str__(self):
        if self.is_active:
            return self.name
        return '%s [inactive]' % self.name


class OAuth2AccessToken(oa2_models.AbstractAccessToken):
    class Meta:
        verbose_name = 'access token'

    host_label = models.CharField(max_length=255, unique=False, blank=True)
    subclient = models.CharField(max_length=255, unique=False, blank=True)
