import logging

from django.http import JsonResponse
from oauth2_provider.decorators import protected_resource

log = logging.getLogger(__name__)


@protected_resource()
def user_info(request):
    """Returns JSON info about the current user."""

    user = request.resource_owner

    # This is returned as dict to be compatible with the old
    # Flask-based Blender ID implementation.
    public_roles = {role.name: True
                    for role in user.roles.all()
                    if role.is_active}

    return JsonResponse({'id': user.id,
                         'full_name': user.get_full_name(),
                         'email': user.email,
                         'roles': public_roles})
