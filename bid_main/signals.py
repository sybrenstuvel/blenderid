"""Handling of Django signals."""

import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

log = logging.getLogger(__name__)


@receiver(post_save)
def autocreate_user_profile(sender, instance, created, **kwargs):
    if sender is not User:
        return

    log.debug('Responding to saving of user ')
    if not created:
        log.debug('User was saved, but not created, not doing anything.')
        return

    if hasattr(instance, 'profile'):
        log.debug('Created user already has a profile, not doing anything.')
        return

    log.info('Creating user profile object for new user %s', instance)

    from . import models
    profile = models.UserProfile(user=instance)
    profile.full_name = instance.get_full_name()
    profile.save()
