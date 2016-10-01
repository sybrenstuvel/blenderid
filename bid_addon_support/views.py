import logging
import datetime

from django.conf import settings
from django.shortcuts import render
from django.views.generic import View
from django.views.decorators.http import require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth import authenticate
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core import exceptions as django_exc

from oauth2_provider.models import AccessToken, RefreshToken, Application
from oauth2_provider.settings import oauth2_settings

import oauthlib.common

# Braces is a dependency of oauth2_provider.
from braces.views import CsrfExemptMixin

def index(request):
    return HttpResponse('This is an API end-point for the Blender ID add-on.')


class SpecialSnowflakeMixin:
    token_scopes = ''  # See AccessToken.scope
    application_id = settings.BLENDER_ID_ADDON_CLIENT_ID
    expires_days = 365  # TODO: move to settings

    @property
    def application(self) -> Application:
        app = getattr(self, '_application', None)
        if app:
            return app

        app = Application.objects.get(client_id=self.application_id)
        self._application = app
        return app


class VerifyIdentityView(SpecialSnowflakeMixin, CsrfExemptMixin, View):
    log = logging.getLogger('%s.VerifyIdentityView' % __name__)

    @method_decorator(sensitive_post_parameters('password'))
    def post(self, request):
        """Entry point that generates an authentication token, given exsiting
        and valid username and password. The token can be used as alternative
        authentication system for REST based services (e.g. Attract).
        """

        username = request.POST['username']
        password = request.POST['password']
        host_label = request.POST['host_label']

        user = authenticate(username=username, password=password)

        if not user or not user.is_active:
            # TODO Throttle authentication attempts (limit to 3 or 5)
            # We need to address the following cases:
            # - the user already has a token-host_label pair
            # - the user never autheticated before (where do we store such info?)
            self.log.info('User %r used bad password', username)
            return JsonResponse({'status': 'fail', 'data': {'password': 'Wrong password'}})

        token, refresh_token = self.create_oauth_token(user, host_label)

        return JsonResponse({
            'status': 'success',
            'data': {
                'user_id': user.id,
                'oauth_token': {
                    'access_token': token.token,
                    'refresh_token': refresh_token.token,
                    'expires': token.expires,
                },
            },
        })

    def create_oauth_token(self, user, host_label) -> (AccessToken, RefreshToken):
        expires = timezone.now() + datetime.timedelta(days=self.expires_days)
        token = AccessToken(
            user=user,
            token=oauthlib.common.generate_token(),
            application=self.application,
            expires=expires,
            scope=self.token_scopes)
        token.save()

        refresh_token = RefreshToken(
            user=user,
            token=oauthlib.common.generate_token(),
            application=self.application,
        )

        return token, refresh_token


class DeleteTokenView(SpecialSnowflakeMixin, CsrfExemptMixin, View):
    log = logging.getLogger('%s.DeleteTokenView' % __name__)

    @method_decorator(sensitive_post_parameters('token'))
    def post(self, request):
        user_id = int(request.POST['user_id'])
        token_string = request.POST['token']

        token = AccessToken.objects.get(token=token_string)
        if token.user.id != user_id:
            return JsonResponse({
                'status': 'fail',
                'data': {'message': 'not your token'}
            })
        token.revoke()

        return JsonResponse({
            'status': 'success',
            'data': {'message': 'ole'}
        })

class ValidateTokenView(SpecialSnowflakeMixin, CsrfExemptMixin, View):
    log = logging.getLogger('%s.ValidateTokenView' % __name__)

    def validate_oauth_token(self, user_id, access_token, subclient) -> AccessToken:
        # FIXME: include subclient check.
        token = AccessToken.objects.get(token=access_token)
        if user_id and token.user.id != user_id:
            raise django_exc.PermissionDenied()

        return token


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
        access_token = request.POST['token']

        token = self.validate_oauth_token(user_id, access_token, subclient)

        if not token or not token.is_valid():
            log.debug('Token not found in database.')
            return JsonResponse({'status': 'fail',
                                 'token': 'Token is invalid'},
                                 status=403)

        user = token.user
        return JsonResponse({'status': 'success',
                        'user': {'id': user.id,
                                 'email': user.email,
                                 'full_name': user.get_full_name().strip()},
                        'token_expires': token.expires,
                        })
