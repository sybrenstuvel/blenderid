from datetime import timedelta

from django.http import HttpResponse
from django.contrib.admin.models import LogEntry
from django.core.urlresolvers import reverse
from django.utils import timezone

from bid_main.models import Role
from .abstract import AbstractAPITest, AccessToken, UserModel


class BadgerBaseTest(AbstractAPITest):
    access_token_scope = 'badger'

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
        response = self.authed_post(url_path, access_token=access_token)
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

        # There should be a log entry describing this change
        entries = list(LogEntry.objects.filter(object_id=self.target_user.id))
        self.assertEqual(1, len(entries))

        # After granting another time, there should still be only one log message.
        response = self.post('bid_api:badger_grant', 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200, f'response: {response}')
        entries = list(LogEntry.objects.filter(object_id=self.target_user.id))
        self.assertEqual(1, len(entries))

    def test_grant_multiple_roles(self):
        response = self.post('bid_api:badger_grant', 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        response = self.post('bid_api:badger_grant', 'badge2', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        response = self.post('bid_api:badger_grant', 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200)

        self.target_user.refresh_from_db()
        self.assertEqual(list(self.target_user.roles.all()), [self.role_badge1, self.role_badge2])

        # There should be a log entry describing each change
        entries = list(LogEntry.objects.filter(object_id=self.target_user.id))
        self.assertEqual(2, len(entries))

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

        # There should be a log entry describing this change
        entries = list(LogEntry.objects.filter(object_id=self.target_user.id))
        self.assertEqual(1, len(entries))

        # After revoking another time, there should still be only one log message.
        response = self.post('bid_api:badger_revoke', 'badge1', self.target_user.email)
        self.assertEqual(response.status_code, 200, f'response: {response}')
        entries = list(LogEntry.objects.filter(object_id=self.target_user.id))
        self.assertEqual(1, len(entries))

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

        # There should be a log entry describing each change, but not the no-ops
        entries = list(LogEntry.objects.filter(object_id=self.target_user.id))
        self.assertEqual(1, len(entries))

    def test_unknown_target_user(self):
        response = self.post('bid_api:badger_revoke', 'badge1', 'unknown@address')
        self.assertEqual(response.status_code, 422)
