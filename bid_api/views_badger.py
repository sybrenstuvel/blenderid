"""
Badger service functionality.
"""

import logging

from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from oauth2_provider.decorators import protected_resource

from bid_main import models as bid_main_models
from .http import HttpResponseNoContent, HttpResponseUnprocessableEntity

log = logging.getLogger(__name__)
UserModel = get_user_model()


def _badger(request, badge: str, email: str, action: str) -> HttpResponse:
    user = request.resource_owner

    # See which roles this user can manage.
    may_manage = {}
    for role in user.roles.all():
        for manage_role in role.may_manage_roles.all():
            may_manage[manage_role.name] = manage_role

    if badge not in may_manage:
        log.warning('User %s tried to %s badge %r to user %s, is not allowed to grant that badge.',
                    user, action, badge, email)
        return HttpResponseForbidden()

    # Try to find the target user.
    try:
        target_user: bid_main_models.User = UserModel.objects.get(email=email)
    except UserModel.DoesNotExist:
        log.warning('User %s tried to %s badge %r to nonexistant user %s.', user, action, badge, email)
        return HttpResponseUnprocessableEntity()

    # Check the role for being an active badge.
    role = may_manage[badge]
    if not role.is_badge:
        log.warning('User %s tried to %s non-badge role %r to user %s.', user, action, badge, email)
        return HttpResponseForbidden()
    if not role.is_active:
        log.warning('User %s tried to %s non-active badge %r to user %s.', user, action, badge, email)
        return HttpResponseForbidden()

    # Grant/revoke the role to/from the target user.
    if action == 'grant':
        log.info('User %s grants badge %r to user %s.', user, badge, email)
        target_user.roles.add(role)
    elif action == 'revoke':
        log.info('User %s revokes badge %r from user %s.', user, badge, email)
        target_user.roles.remove(role)

    target_user.save()

    return HttpResponseNoContent()


@protected_resource()
@require_http_methods(['POST'])
def badger_grant(request, badge, email) -> HttpResponse:
    return _badger(request, badge, email, 'grant')


@protected_resource()
@require_http_methods(['POST'])
def badger_revoke(request, badge, email) -> HttpResponse:
    return _badger(request, badge, email, 'revoke')
