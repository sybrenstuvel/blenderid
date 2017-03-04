"""
Badger service functionality.
"""

import logging

from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import get_user_model
from oauth2_provider.decorators import protected_resource

log = logging.getLogger(__name__)
UserModel = get_user_model()


@protected_resource()
def badger_grant(request, badge, email) -> HttpResponse:
    user = request.resource_owner

    # See which roles this user can manage.
    may_manage = {}
    for role in user.roles.all():
        for manage_role in role.may_manage_roles.all():
            may_manage[manage_role.name] = manage_role

    if badge not in may_manage:
        log.warning('User %s tried to grant badge %r to user %s, is not allowed to grant that badge.',
                    user, badge, email)
        return HttpResponseForbidden()

    # Try to find the target user.
    try:
        target_user = UserModel.objects.get(email=email)
    except UserModel.DoesNotExist:
        log.warning('User %s tried to grant badge %r to nonexistant user %s.', user, badge, email)
        return HttpResponse(status=422)

    # Check the role for being an active badge.
    role = may_manage[badge]
    if not role.is_badge:
        log.warning('User %s tried to grant non-badge role %r to user %s.', user, badge, email)
        return HttpResponseForbidden()
    if not role.is_active:
        log.warning('User %s tried to grant non-active badge %r to user %s.', user, badge, email)
        return HttpResponseForbidden()

    # Assign the role to the target user.
    log.info('User %s grants badge %r to user %s.', user, badge, email)
    target_user.roles.add(role)
    target_user.save()

    return HttpResponse()
