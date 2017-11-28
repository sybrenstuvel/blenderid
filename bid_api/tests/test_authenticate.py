from datetime import timedelta
import json

from django.http import HttpResponse
from django.contrib.admin.models import LogEntry
from django.core.urlresolvers import reverse
from django.utils import timezone

from .abstract import AbstractAPITest, AccessToken, UserModel


class AuthenticateTest(AbstractAPITest):
    access_token_scope = 'authenticate'
    test_password = '3444443'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = UserModel.objects.create_user(
            'another@user.com',
            cls.test_password,
            id=640509,
            full_name='Fuuull Ñame',
        )

    def post(self, data: dict, *, access_token='') -> HttpResponse:
        url_path = reverse('bid_api:authenticate')
        response = self.authed_post(url_path, data=data, access_token=access_token)
        return response

    def test_authenticate_happy(self):
        response = self.post({
            'email': self.auth_user.email,
            'password': self.test_password,
        })
        self.assertEqual(200, response.status_code, f'response: {response}')
        self.assertEqual('application/json', response.get('content-type'))

        payload = json.loads(response.content)
        self.assertEqual({
            'user_id': self.auth_user.id,
            'full_name': self.auth_user.full_name,
            'email': self.auth_user.email,
        }, payload)

    def test_authenticate_empty(self):
        response = self.post({})
        self.assertEqual(400, response.status_code, f'response: {response}')

        content = response.content.decode(response['content-type'])
        self.assertNotIn(str(self.auth_user.id), content)
        self.assertNotIn(self.auth_user.full_name, content)
        self.assertNotIn(self.auth_user.email, content)

    def test_authenticate_bad_password(self):
        response = self.post({
            'email': self.auth_user.email,
            'password': self.test_password + 'ü',
        })
        self.assertEqual(403, response.status_code, f'response: {response}')
        self.assertEqual('application/json', response.get('content-type'))

        payload = json.loads(response.content)
        self.assertEqual({'error': 'badpw'}, payload)

    def test_authenticate_nonexistant_email(self):
        response = self.post({
            'email': f'nodbody+{self.auth_user.email}',
            'password': self.test_password,
        })
        self.assertEqual(403, response.status_code, f'response: {response}')
        self.assertEqual('application/json', response.get('content-type'))

        payload = json.loads(response.content)
        self.assertEqual({'error': 'badpw'}, payload)

    def test_authenticate_bad_token_scope(self):
        wrong_token = AccessToken.objects.create(
            user=self.user,
            scope='email',
            expires=timezone.now() + timedelta(seconds=300),
            token='token-with-wrong-scope',
            application=self.application
        )
        wrong_token.save()

        response = self.post({
            'email': f'nodbody+{self.auth_user.email}',
            'password': self.test_password,
        }, access_token=wrong_token.token)
        self.assertEqual(403, response.status_code, f'response: {response}')
