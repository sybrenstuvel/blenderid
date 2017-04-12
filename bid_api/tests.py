from datetime import timedelta

from django.core.handlers.wsgi import WSGIRequest
from django.test import TestCase, RequestFactory
from django.utils import timezone

from django.contrib.auth import get_user_model

from oauth2_provider.models import get_application_model, AccessToken

from bid_main.models import Role

Application = get_application_model()
UserModel = get_user_model()


class BaseTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request_factory = RequestFactory()
        super(BaseTest, cls).setUpClass()

    def setUp(self):
        self.user = UserModel.objects.create_user('test@user.com', '123456')

        self.application = Application.objects.create(
            name="test_client_credentials_app",
            user=self.user,
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )

        self.access_token = AccessToken.objects.create(
            user=self.user,
            scope='read write',
            expires=timezone.now() + timedelta(seconds=300),
            token='secret-access-token-key',
            application=self.application
        )

    def tearDown(self):
        self.access_token.delete()
        self.application.delete()
        self.user.delete()

    def authed_request(self) -> WSGIRequest:
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + self.access_token.token,
        }
        request = self.request_factory.get('/fake-resource', **auth_headers)
        return request


class BadgerBaseTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.role_notallowed = Role.objects.create(name='not-allowed-badge', is_badge=True)
        cls.role_notabadge = Role.objects.create(name='not-badge', is_badge=False)
        cls.role_inactivebadge = Role.objects.create(name='inactive-badge', is_badge=True, is_active=False)
        cls.role_badge1 = Role.objects.create(name='badge1', is_badge=True)
        cls.role_badge2 = Role.objects.create(name='badge2', is_badge=True)
        cls.role_badger = Role.objects.create(name='badger', is_badge=False)

        # Role needs to be saved before assigning many-to-many fields.
        cls.role_badger.may_manage_roles = [cls.role_notabadge,
                                            cls.role_badge1,
                                            cls.role_badge2,
                                            cls.role_inactivebadge]
        cls.role_badger.save()


class BadgerApiGrantTest(BadgerBaseTest):
    def setUp(self):
        super().setUp()

        self.user.roles = [self.role_badger]
        self.user.save()

        self.target_user = UserModel.objects.create_user('target@user.com', '123456')

    def test_grant_unknown_badge(self):
        from .views_badger import badger_grant

        request = self.authed_request()
        response = badger_grant(request, 'unknown-badge', self.target_user.email)

        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [])

    def test_grant_not_allowed_badge(self):
        from .views_badger import badger_grant

        request = self.authed_request()
        response = badger_grant(request, 'not-allowed-badge', self.target_user.email)

        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [])

    def test_grant_inactive_badge(self):
        from .views_badger import badger_grant

        request = self.authed_request()
        response = badger_grant(request, 'inactive-badge', self.target_user.email)

        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [])

    def test_grant_happy_flow(self):
        from .views_badger import badger_grant

        request = self.authed_request()
        response = badger_grant(request, 'badge1', self.target_user.email)

        self.assertEqual(response.status_code, 200)

        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [self.role_badge1])

    def test_grant_multiple_roles(self):
        from .views_badger import badger_grant

        request = self.authed_request()
        response = badger_grant(request, 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        response = badger_grant(request, 'badge2', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        response = badger_grant(request, 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [self.role_badge1, self.role_badge2])

    def test_unknown_target_user(self):
        from .views_badger import badger_grant

        request = self.authed_request()
        response = badger_grant(request, 'badge1', 'unknown@address')

        self.assertEqual(response.status_code, 422)


class BadgerApiRevokeTest(BadgerBaseTest):
    def setUp(self):
        super().setUp()

        self.user.roles = [self.role_badger]
        self.user.save()

        # Incorrectly assign many roles, so that we can test what happens when they are
        # actually there and then revoked.
        self.target_user = UserModel.objects.create_user('target@user.com', '123456')
        self.assigned_roles = {self.role_notallowed, self.role_notabadge, self.role_inactivebadge, self.role_badge1}
        self.target_user.roles = list(self.assigned_roles)

    def test_revoke_unknown_badge(self):
        from .views_badger import badger_revoke

        request = self.authed_request()
        response = badger_revoke(request, 'unknown-badge', self.target_user.email)

        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(set(self.target_user.roles.all()), self.assigned_roles)

    def test_revoke_not_allowed_badge(self):
        from .views_badger import badger_revoke

        request = self.authed_request()
        response = badger_revoke(request, 'not-allowed-badge', self.target_user.email)

        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(set(self.target_user.roles.all()), self.assigned_roles)

    def test_revoke_inactive_badge(self):
        from .views_badger import badger_revoke

        request = self.authed_request()
        response = badger_revoke(request, 'inactive-badge', self.target_user.email)

        self.assertEqual(response.status_code, 403)
        self.target_user.refresh_from_db()
        self.assertEqual(set(self.target_user.roles.all()), self.assigned_roles)

    def test_revoke_happy_flow(self):
        from .views_badger import badger_revoke

        request = self.authed_request()
        response = badger_revoke(request, 'badge1', self.target_user.email)

        self.assertEqual(response.status_code, 200)

        self.target_user.refresh_from_db()
        self.assertEqual(set(self.target_user.roles.all()),
                         {self.role_notallowed, self.role_notabadge, self.role_inactivebadge})

    def test_revoke_multiple_roles(self):
        from .views_badger import badger_revoke

        request = self.authed_request()
        response = badger_revoke(request, 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        response = badger_revoke(request, 'badge2', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        response = badger_revoke(request, 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        self.target_user.refresh_from_db()
        self.assertEqual(set(self.target_user.roles.all()),
                         {self.role_notallowed, self.role_notabadge, self.role_inactivebadge})

    def test_unknown_target_user(self):
        from .views_badger import badger_revoke

        request = self.authed_request()
        response = badger_revoke(request, 'badge1', 'unknown@address')

        self.assertEqual(response.status_code, 422)
