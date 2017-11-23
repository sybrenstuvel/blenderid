from datetime import timedelta

from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

import oauth2_provider.models as oa2_models

from bid_main.models import Role

Application = oa2_models.get_application_model()
AccessToken = oa2_models.get_access_token_model()
UserModel = get_user_model()


class BaseTest(TestCase):
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
            scope='badger',
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

    def authed(self, method: str, path: str = '/does-not-matter', *, access_token='',
               **kwargs) -> HttpResponse:
        if not access_token:
            access_token = self.access_token.token
        kwargs['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        return self.client.generic(method, path, **kwargs)


class BadgerBaseTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.role_notallowed = Role.objects.create(name='not-allowed-badge', is_badge=True)
        cls.role_notabadge = Role.objects.create(name='not-badge', is_badge=False)
        cls.role_inactivebadge = Role.objects.create(name='inactive-badge', is_badge=True,
                                                     is_active=False)
        cls.role_badge1 = Role.objects.create(name='badge1', is_badge=True)
        cls.role_badge2 = Role.objects.create(name='badge2', is_badge=True)
        cls.role_badger = Role.objects.create(name='badger', is_badge=False)

        # Role needs to be saved before assigning many-to-many fields.
        cls.role_badger.may_manage_roles = [cls.role_notabadge,
                                            cls.role_badge1,
                                            cls.role_badge2,
                                            cls.role_inactivebadge]
        cls.role_badger.save()

    def post(self, view_name: str, badge: str, email: str, *, access_token='') -> HttpResponse:
        url_path = reverse(view_name, kwargs={'badge': badge, 'email': email})
        response = self.authed('POST', url_path, access_token=access_token)
        return response


class BadgerApiGrantTest(BadgerBaseTest):
    def setUp(self):
        super().setUp()

        self.user.roles = [self.role_badger]
        self.user.save()

        self.target_user = UserModel.objects.create_user('target@user.com', '123456')

    def test_grant_unknown_badge(self):
        response = self.post('bid_api:badger_grant', 'unknown-badge', self.target_user.email)
        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [])

    def test_grant_not_allowed_badge(self):
        response = self.post('bid_api:badger_grant', 'not-allowed-badge', self.target_user.email)
        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [])

    def test_grant_inactive_badge(self):
        response = self.post('bid_api:badger_grant', 'inactive-badge', self.target_user.email)
        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [])

    def test_grant_happy_flow(self):
        response = self.post('bid_api:badger_grant', 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200, f'response: {response}')
        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [self.role_badge1])

    def test_grant_multiple_roles(self):
        response = self.post('bid_api:badger_grant', 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        response = self.post('bid_api:badger_grant', 'badge2', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        response = self.post('bid_api:badger_grant', 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [self.role_badge1, self.role_badge2])

    def test_unknown_target_user(self):
        response = self.post('bid_api:badger_grant', 'badge1', 'unknown@address')
        self.assertEqual(response.status_code, 422)

    def test_wrong_token_scope(self):
        wrong_token = AccessToken.objects.create(
            user=self.user,
            scope='email',
            expires=timezone.now() + timedelta(seconds=300),
            token='token-with-wrong-scope',
            application=self.application
        )
        wrong_token.save()
        response = self.post('bid_api:badger_grant', 'badge1', self.target_user.email,
                             access_token=wrong_token.token)
        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [])


class BadgerApiRevokeTest(BadgerBaseTest):
    def setUp(self):
        super().setUp()

        self.user.roles = [self.role_badger]
        self.user.save()

        # Incorrectly assign many roles, so that we can test what happens when they are
        # actually there and then revoked.
        self.target_user = UserModel.objects.create_user('target@user.com', '123456')
        self.assigned_roles = {self.role_notallowed, self.role_notabadge, self.role_inactivebadge,
                               self.role_badge1}
        self.target_user.roles = list(self.assigned_roles)

    def test_revoke_unknown_badge(self):
        response = self.post('bid_api:badger_revoke', 'unknown-badge', self.target_user.email)
        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(set(self.target_user.roles.all()), self.assigned_roles)

    def test_revoke_not_allowed_badge(self):
        response = self.post('bid_api:badger_revoke', 'not-allowed-badge', self.target_user.email)
        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(set(self.target_user.roles.all()), self.assigned_roles)

    def test_revoke_inactive_badge(self):
        response = self.post('bid_api:badger_revoke', 'inactive-badge', self.target_user.email)
        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(set(self.target_user.roles.all()), self.assigned_roles)

    def test_revoke_happy_flow(self):
        response = self.post('bid_api:badger_revoke', 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertEqual(set(self.target_user.roles.all()),
                         {self.role_notallowed, self.role_notabadge, self.role_inactivebadge})

    def test_revoke_multiple_roles(self):
        response = self.post('bid_api:badger_revoke', 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        response = self.post('bid_api:badger_revoke', 'badge2', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        response = self.post('bid_api:badger_revoke', 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        self.target_user.refresh_from_db()
        self.assertEqual(set(self.target_user.roles.all()),
                         {self.role_notallowed, self.role_notabadge, self.role_inactivebadge})

    def test_unknown_target_user(self):
        response = self.post('bid_api:badger_revoke', 'badge1', 'unknown@address')
        self.assertEqual(response.status_code, 422)
