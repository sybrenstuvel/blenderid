from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from oauth2_provider.models import get_access_token_model, get_refresh_token_model

AccessToken = get_access_token_model()
RefreshToken = get_refresh_token_model()


# We don't import django.contrib.auth.models.User directly. Instead, we use
# django.contrib.auth.get_user_model() as described at:
# https://docs.djangoproject.com/en/1.9/topics/auth/customizing/

class BlenderIdAddonSupportTest(TestCase):
    fixtures = ['bid_addon_support/fixtures/bid_addon_support']

    def setUp(self):
        self._create_user()

    def test_verify_identity_happy(self):
        """
        Happy flow of the Blender ID add-on authentication.
        """

        url = reverse('addon_support:identify')
        resp = self.client.post(url, {
            'email': 'sybren@example.com',
            'password': 'jemoeder',
            'host_label': 'unittest',
        })
        self.assertEquals(200, resp.status_code)

        data = resp.json()
        self.assertEquals('success', data['status'])
        token_data = data['data']['oauth_token']

        # There must be a token with the given information
        dbtoken = AccessToken.objects.get(token=token_data['access_token'])
        self.assertIsNotNone(dbtoken)

        return dbtoken

    def test_verify_identity_happy_username(self):
        """
        Happy flow of the Blender ID add-on authentication using 'username' form field.
        """

        url = reverse('addon_support:identify')
        resp = self.client.post(url, {
            'username': 'sybren@example.com',
            'password': 'jemoeder',
            'host_label': 'unittest',
        })
        self.assertEquals(200, resp.status_code)

        data = resp.json()
        self.assertEquals('success', data['status'])

    def test_verify_identity_bad_password(self):
        """
        Bad password given
        """

        url = reverse('addon_support:identify')
        resp = self.client.post(url, {
            'email': 'sybren@stuvel.eu',
            'password': 'bad password ẅïẗḧ üñïčöđë',
            'host_label': 'unittest',
        })
        self.assertEquals(200, resp.status_code)

        data = resp.json()
        self.assertEquals('fail', data['status'])
        self.assert_no_tokens()

    def _create_user(self):
        user_cls = get_user_model()
        user = user_cls.objects.create_user(email='sybren@example.com',
                                            password='jemoeder',
                                            full_name='Sybren Stüvel')
        user.save()

    def test_verify_identity_bad_username(self):
        """
        Bad password given
        """

        url = reverse('addon_support:identify')
        resp = self.client.post(url, {
            'username': 'othername',
            'password': 'jemoeder',
            'host_label': 'unittest',
        })
        self.assertEquals(200, resp.status_code)

        data = resp.json()
        self.assertEquals('fail', data['status'])
        self.assert_no_tokens()

    def assert_no_tokens(self):
        self.assertEquals([], list(AccessToken.objects.all()))
        self.assertEquals([], list(RefreshToken.objects.all()))

    def test_delete_token(self):
        # First make sure there is a token.
        dbtoken = self.test_verify_identity_happy()

        url = reverse('addon_support:delete_token')
        resp = self.client.post(url, {
            'user_id': dbtoken.user.id,
            'token': dbtoken.token,
        })
        self.assertEquals(200, resp.status_code)
        self.assert_no_tokens()

    def test_validate_token_happy(self):
        # First make sure there is a token.
        dbtoken = self.test_verify_identity_happy()

        url = reverse('addon_support:validate_token')
        resp = self.client.post(url, {
            'token': dbtoken.token,
        })
        self.assertEquals(200, resp.status_code)

        data = resp.json()
        self.assertEquals('success', data['status'])
        self.assertEquals(dbtoken.user.id, data['user']['id'])
        self.assertEquals('sybren@example.com', data['user']['email'])
        self.assertEquals('Sybren Stüvel', data['user']['full_name'])
