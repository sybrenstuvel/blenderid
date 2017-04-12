"""
API for the Blender Store.

This allows the Blender Store to create & authenticate users.
"""

import logging

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from oauth2_provider.decorators import protected_resource

from bid_main import models as bid_main_models
from .forms import StoreAPICreateUserForm

log = logging.getLogger(__name__)
UserModel = get_user_model()


@protected_resource()
@require_http_methods(['POST'])
def create_user(request) -> HttpResponse:
    user = request.resource_owner

    if not user.has_perm('bid_main.use_store_api'):
        log.warning('User %s tried to use the store API to create a user, '
                    'but does not have the required permission.', user)
        return HttpResponseForbidden()

    form = StoreAPICreateUserForm(request.POST)
    if not form.is_valid():
        return JsonResponse(form.errors.as_data(), status=422)


    return HttpResponse()
