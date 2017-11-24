import logging

from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.forms import ModelForm
from oauth2_provider.decorators import protected_resource

from .abstract import AbstractAPIView

UserModel = get_user_model()


class CreateUserForm(ModelForm):
    """User creation form, using fields from UserModel."""

    class Meta:
        model = UserModel
        fields = ['email', 'full_name', 'password']

    def clean_password(self):
        password = self.cleaned_data['password'].strip()

        # Prefix with 'blenderid$' if not specified by the caller.
        if not password.startswith('blenderid$'):
            password = f'blenderid${password}'

        # Replace BCrypt hash method to what Django expects.
        if password.startswith('blenderid$$2a$') or password.startswith('blenderid$$2y$'):
            password = f'blenderid$$2b${password[14:]}'

        return password


class CreateUserView(AbstractAPIView):
    log = logging.getLogger(f'{__name__}.CreateUser')

    @method_decorator(protected_resource(scopes=['usercreate']))
    @transaction.atomic()
    def post(self, request) -> HttpResponse:
        cuf = CreateUserForm(request.POST)
        if not cuf.is_valid():
            errors = cuf.errors.as_json()
            self.log.warning('invalid form received: %s', errors)
            return HttpResponse(errors, content_type='application/json', status=400)

        self.log.info('Creating user %r on behalf of %s', request.POST['email'], request.user)
        db_user = cuf.save()

        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(UserModel).pk,
            object_id=db_user.id,
            object_repr=str(db_user),
            action_flag=ADDITION,
            change_message='Account created via user creation API.')

        return JsonResponse({'user_id': db_user.id}, status=201)
