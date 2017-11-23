"""
Badger service functionality.
"""

import logging

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.admin.models import LogEntry, ADDITION, DELETION
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.decorators import protected_resource

from bid_main import models as bid_main_models
from ..http import HttpResponseUnprocessableEntity

log = logging.getLogger(__name__)
UserModel = get_user_model()


class BadgerView(View):
    action = 'grant'

    @method_decorator(protected_resource(scopes=['badger']))
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, badge: str, email: str) -> HttpResponse:
        user = request.user
        action = self.action

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
            action_flag = ADDITION
            if role in target_user.roles.all():
                log.debug('User %s already has badge %r', email, badge)
                return JsonResponse({'result': 'no-op'})
            target_user.roles.add(role)
            change_message = f'granted badge {badge}'
        elif action == 'revoke':
            log.info('User %s revokes badge %r from user %s.', user, badge, email)
            action_flag = DELETION
            if role not in target_user.roles.all():
                log.debug('User %s already does not have badge %r', email, badge)
                return JsonResponse({'result': 'no-op'})
            target_user.roles.remove(role)
            change_message = f'revoked badge {badge}'
        else:
            log.warning('unknown action %r', action)
            return HttpResponseUnprocessableEntity('unknown action')
        target_user.save()

        LogEntry.objects.log_action(
            user_id=user.id,
            content_type_id=ContentType.objects.get_for_model(UserModel).pk,
            object_id=target_user.id,
            object_repr=str(target_user),
            action_flag=action_flag,
            change_message=change_message)

        return JsonResponse({'result': 'ok'})
