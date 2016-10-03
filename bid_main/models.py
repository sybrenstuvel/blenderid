import math
from django.db import models
from django.conf import settings
from django_countries.fields import CountryField


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='profile')
    # Instead of storing first & last name separately, we want a true 'full_name' field.
    # So DO NOT USE User.get_full_name(), as this will return 'first_name last_name'
    full_name = models.CharField(max_length=255, blank=True)
    confirmed_email_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    current_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return 'Profile of %s' % self.full_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # Updates the user's first_name and last_name from full_name, so that
        # the admin interface can search for users by name. By no means is this
        # culturally correct, and those fields shouldn't be used by any front-end code.
        name_parts = self.full_name.split(' ')
        midpoint = int(math.ceil(len(name_parts) / 2))

        self.user.first_name = ' '.join(name_parts[:midpoint])
        self.user.last_name = ' '.join(name_parts[midpoint:])
        self.user.save()


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
        return '[Setting %r]' % self.name


class UserSetting(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    setting = models.ForeignKey(Setting, on_delete=models.CASCADE)
    unconstrained_value = SettingValueField()

    def __str__(self):
        return '[UserSetting of %r; %r = %r]' % (self.user.username, self.setting.name, self.unconstrained_value)


ADDRESS_TYPE_CHOICES = [
    ('billing', 'Billing'),
    ('shipping', 'Shipping'),
]


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='addresses')
    address_type = models.CharField(max_length=32, choices=ADDRESS_TYPE_CHOICES)
    address = models.TextField(max_length=255)
    country = CountryField()

    def __str__(self):
        return '[Address of %r; %s]' % (self.user.full_name, self.address_type)
