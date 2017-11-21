import datetime
import logging
import typing

from django.conf import settings
from django.views.generic import View
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core import exceptions as django_exc

import oauth2_provider.models as oa2_models
from oauth2_provider.views.generic import ProtectedResourceView

import oauthlib.common

# Braces is a dependency of oauth2_provider.
from braces.views import CsrfExemptMixin

AccessToken = oa2_models.get_access_token_model()
RefreshToken = oa2_models.get_refresh_token_model()
Application = oa2_models.get_application_model()

# Oops, I (Sybren) made a mistake in the Blender ID add-on and used the
# wrong datetime format string to parse the new format. Can't easily
# change the add-on as it's bundled with Blender, so for now let's use
# the expected format for the expiry date here.
EXPIRY_DATE_FMT = '%Y-%m-%dT%H:%M:%S.%fZ'


def index(request):
    return HttpResponse('This is an API end-point for the Blender ID add-on.')


class HttpResponseUnauthorized(HttpResponse):
    status_code = 401


class SpecialSnowflakeMixin:
    token_scopes = ''  # See AccessToken.scope
    application_id = settings.BLENDER_ID_ADDON_CLIENT_ID
    expires_days = 365  # TODO: move to settings
    log = logging.getLogger('%s.SpecialSnowflakeMixin' % __name__)

    @property
    def application(self) -> Application:
        app = getattr(self, '_application', None)
        if app:
            return app

        try:
            app = Application.objects.get(client_id=self.application_id)
        except Application.DoesNotExist:
            self.log.error('Special snowflake OAuth app %r does not exist', self.application_id)
            raise django_exc.ImproperlyConfigured('Server-side OAuth configuration error.')

        self._application = app
        return app

    def create_oauth_token(self, user, host_label: str, subclient='') -> (
            AccessToken, RefreshToken):
        """Creates an OAuth token and stores it in the database."""
        expires = timezone.now() + datetime.timedelta(days=self.expires_days)
        token = AccessToken(
            user=user,
            token=oauthlib.common.generate_token(),
            application=self.application,
            expires=expires,
            scope=self.token_scopes,
            host_label=host_label,
            subclient=subclient or '')
        token.save()

        refresh_token = RefreshToken(
            user=user,
            token=oauthlib.common.generate_token(),
            application=self.application,
        )

        return token, refresh_token

    def validate_oauth_token(self, user_id: int, access_token: str = '', subclient: str = '') \
            -> typing.Optional[AccessToken]:
        try:
            token = AccessToken.objects.get(token=access_token, subclient=subclient or '')
        except AccessToken.DoesNotExist:
            self.log.debug('Token not found in database.')
            return None

        if user_id and token.user.id != user_id:
            self.log.warning('Token is owned by user %s but user %s is validating it',
                             token.user_id, user_id)
            raise django_exc.PermissionDenied()

        if not token.is_valid():
            self.log.debug('Token is found but not valid.')
            return None

        return token

    def fmt_expires(self, expiry: datetime.datetime) -> str:
        """Formats the expiry datetime of an access token."""

        return expiry.strftime(EXPIRY_DATE_FMT)


class VerifyIdentityView(SpecialSnowflakeMixin, CsrfExemptMixin, View):
    log = logging.getLogger('%s.VerifyIdentityView' % __name__)

    @method_decorator(sensitive_post_parameters('password'))
    def post(self, request):
        """Entry point that generates an authentication token, given exsiting
        and valid email and password. The token can be used as alternative
        authentication system for REST based services (e.g. Attract).
        """

        # gradually move from POST['username'] to POST['email']
        email = request.POST.get('email')
        if not email:
            email = request.POST.get('username')
        if not email:
            return JsonResponse({'status': 'fail', 'data': {'email': 'not given'}})

        password = request.POST['password']
        host_label = request.POST['host_label']

        user = authenticate(email=email, password=password)

        if not user or not user.is_active:
            # TODO Throttle authentication attempts (limit to 3 or 5)
            # We need to address the following cases:
            # - the user already has a token-host_label pair
            # - the user never autheticated before (where do we store such info?)
            self.log.info('User %r used bad password', email)
            return JsonResponse({'status': 'fail', 'data': {'password': 'Wrong password'}})

        token, refresh_token = self.create_oauth_token(user, host_label)

        return JsonResponse({
            'status': 'success',
            'data': {
                'user_id': user.id,
                'oauth_token': {
                    'access_token': token.token,
                    'refresh_token': refresh_token.token,
                    'expires': self.fmt_expires(token.expires),
                },
            },
        })


class DeleteTokenView(SpecialSnowflakeMixin, CsrfExemptMixin, View):
    log = logging.getLogger('%s.DeleteTokenView' % __name__)

    @method_decorator(sensitive_post_parameters('token'))
    def post(self, request):
        user_id = int(request.POST['user_id'])
        token_string = request.POST['token']
        subclient = request.POST.get('subclient_id', '')

        token = self.validate_oauth_token(user_id, token_string, subclient)
        if not token:
            return HttpResponseUnauthorized()
        token.revoke()

        return JsonResponse({
            'status': 'success',
            'data': {'message': 'ole'}
        })


class ValidateTokenView(SpecialSnowflakeMixin, CsrfExemptMixin, View):
    log = logging.getLogger('%s.ValidateTokenView' % __name__)

    @method_decorator(sensitive_post_parameters('token'))
    def post(self, request):
        """Validate and existing authentication token.

        This is usually called by a third party (e.g. Attract) every few requests
        to confirm the identity of a user.

        Returns further information about the user if the given token is valid.

        The user ID is not used at the moment. The subclient ID can be empty or
        absent from the request, in which a regular OAuth token is verified. If
        the subclient is present, a subclient token is verified.
        """

        subclient = request.POST.get('subclient_id')
        user_id = request.POST.get('user_id')
        if user_id:
            try:
                user_id = int(user_id)
            except TypeError:
                return HttpResponseBadRequest(f'invalid user ID {user_id!r}')

        access_token = request.POST['token']

        token = self.validate_oauth_token(user_id, access_token, subclient)
        if not token or not token.is_valid():
            return JsonResponse({'status': 'fail',
                                 'token': 'Token is invalid'},
                                status=403)

        user = token.user
        return JsonResponse({'status': 'success',
                             'user': {'id': user.id,
                                      'email': user.email,
                                      'full_name': user.get_full_name().strip()},
                             'token_expires': self.fmt_expires(token.expires),
                             })


class SubclientCreateToken(SpecialSnowflakeMixin, CsrfExemptMixin, LoginRequiredMixin,
                           ProtectedResourceView):
    """Creates a subclient token by storing the subclient ID in the token scope."""
    log = logging.getLogger('%s.SubclientCreateToken' % __name__)
    raise_exception = True  # don't redirect to the login page.

    @method_decorator(sensitive_post_parameters('token'))
    def post(self, request):
        """Creates a subclient token for the user."""

        subclient = request.POST['subclient_id']
        host_label = request.POST.get('host_label', '')

        scst, _ = self.create_oauth_token(request.user, host_label, subclient)
        return JsonResponse({
            'status': 'success',
            'data': {
                'token': scst.token,
                'expires': self.fmt_expires(scst.expires),
            }
        }, status=201)
