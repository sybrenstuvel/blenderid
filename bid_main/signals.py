import logging

from django.core.signals import got_request_exception
from django.dispatch import receiver

log = logging.getLogger(__name__)


@receiver(got_request_exception)
def log_exception(sender, **kwargs):
    log.exception('uncaught exception occurred')
