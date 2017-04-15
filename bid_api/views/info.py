import logging

from django.http import JsonResponse
from oauth2_provider.decorators import protected_resource

log = logging.getLogger(__name__)


@protected_resource()
def user_info(request):
    """Returns JSON info about the current user."""

    user = request.resource_owner

    # Ensure that some roles are set to False when not there.
    public_roles = {
        'bfct_trainer': False,
        'network_member': False}

    # The remaining roles are added only when granted.
    for group in user.groups.all():
        public_roles[group.name] = True

    return JsonResponse({'id': user.id,
                         'full_name': user.get_full_name(),
                         'first_name': user.first_name,
                         'last_name': user.last_name,
                         'email': user.email,
                         'roles': public_roles})
