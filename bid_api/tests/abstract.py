from datetime import timedelta

from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

import oauth2_provider.models as oa2_models

Application = oa2_models.get_application_model()
AccessToken = oa2_models.get_access_token_model()
UserModel = get_user_model()


class AbstractAPITest(TestCase):
    access_token_scope = ''

    @classmethod
    def setUpClass(cls):
        cls.user = UserModel.objects.create_user('test@user.com', '123456')
        cls.application = Application.objects.create(
            name="test_client_credentials_app",
            user=cls.user,
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        cls.access_token = AccessToken.objects.create(
            user=cls.user,
            scope=cls.access_token_scope,
            expires=timezone.now() + timedelta(seconds=300),
            token='secret-access-token-key',
            application=cls.application
        )
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        try:
            cls.access_token.delete()
        except AttributeError:
            pass
        try:
            cls.application.delete()
        except AttributeError:
            pass
        try:
            cls.user.delete()
        except AttributeError:
            pass

    def authed_post(self, path: str, *, access_token='', **kwargs) -> HttpResponse:
        if not access_token:
            access_token = self.access_token.token
        kwargs['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        return self.client.post(path, **kwargs)

    def authed_get(self, path: str, *, access_token='', **kwargs) -> HttpResponse:
        if not access_token:
            access_token = self.access_token.token
        kwargs['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        return self.client.get(path, **kwargs)
