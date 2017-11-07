"""This test case mimicks the behaviour of the Blender ID add-on."""

import datetime
import pytz
import typing
from urllib.parse import urljoin

# noinspection PyPackageRequirements
import dateutil.parser

from abstract_bid_test import AbstractBlenderIDTest

SUBCLIENT = 'PILLAR'


class AddonBehaviourTest(AbstractBlenderIDTest):
    @classmethod
    def setUpClass(cls):
        import getpass
        import os

        super().setUpClass()

        cloud_server = os.environ.get('BCLOUD_SERVER')
        if not cloud_server:
            raise ValueError('Set BCLOUD_SERVER environment variable to the Pillar server')
        cls.cloud_api = urljoin(cloud_server, 'api/')

        cls.username = os.environ.get('BLENDER_ID_UNAME')
        cls.password = os.environ.get('BLENDER_ID_PASSWD')
        if not cls.password:
            print()
            print(f'I need your credentials to test against {cls.endpoint}')
            cls.username = input(f'Username [{cls.username}]: ') or cls.username
            cls.password = getpass.getpass(f'Password for {cls.username}: ')

    def do_identify(self, expected_status='success') -> typing.Optional[dict]:
        """Logs in and returns the 'data' value of the result.

        The result is a dict like: {
            'data': {
                'oauth_token': {
                    'access_token': 'PV8lpmY8ioh6GOokW60emPyo3MBhhr',
                    'expires': 'Wed, 07 Nov 2018 11:01:41 GMT',
                    'refresh_token': 'cN25YjFQxY5wGTdXgGH8O0fTEBZIeC'
                },
                'user_id': 1896
            },
            'status': 'success'
        }

        :param expected_status: either 'success' or 'fail'
        """
        r = self.post('u/identify', data={
            'username': self.username,
            'password': self.password,
            'host_label': 'some integration tester',
        })
        resp = r.json()
        self.assertEqual(expected_status, resp.get('status'), f'response was: {r.text}')

        return resp.get('data')

    def do_validate(self, token: str, subclient='', expected_status='success') -> dict:
        """Validates the given auth token.

        Returns the validation response, which is a dict like this: {
            "status": "success",
            "token_expires": "Wed, 07 Nov 2018 10:59:14 GMT",
            "user": {
                "email": "sybren@stuvel.eu",
                "full_name": "dr. Sybren\u2122 <script>alert('hacked via BlenderID!')</script>",
                "id": 1896
            }
        }
        """

        expected_code = {
            'success': 200,
            'fail': 403,
        }[expected_status]

        payload = {'token': token}
        if subclient:
            payload['subclient_id'] = subclient

        r = self.post('u/validate_token', data=payload, expected_status=expected_code)
        # print(f'Validation returned: {r.text}')
        resp = r.json()
        self.assertEqual(expected_status, resp.get('status'), f'response was: {r.text}')
        return resp

    def do_logout(self, user_id: str, token: str, expected_status='success'):
        """Remotely deletes the token.

        :param expected_status: 'success' or 'fail'
        """
        r = self.post('u/delete_token', data={
            'user_id': user_id,
            'token': token,
        })
        resp = r.json()
        self.assertEqual(expected_status, resp.get('status'), f'response was: {r.text}')

    def do_create_subclient_token(self, token: str, subclient=SUBCLIENT,
                                  expected_status='success') -> dict:
        """Creates a subclient token, returns the response data.

        Returns a dict like: {
            "expires": "Wed, 07 Nov 2018 11:26:45 GMT",
            "token": "b8TWUS5qFl0z2hBTfqxfUtF1eLG8Dz"
        }
        """
        r = self.post('subclients/create_token',
                      data={'subclient_id': subclient,
                            'host_label': 'some integration test'},
                      token=token,
                      expected_status=201)
        # print(f'Subclient token creation: {r.text}')
        resp = r.json()
        self.assertEqual(expected_status, resp['status'], f'response: {r.text}')

        return resp['data']

    def do_revoke_subclient_token(self, user_id: str, token: str, subclient=SUBCLIENT,
                                  expected_status='success'):
        """Revokes a subclient token."""

        expected_code = {
            'success': 200,
            'fail': 401,
        }[expected_status]

        r = self.post('subclients/revoke_token',
                      data={'client_id': 'unknown',
                            'user_id': user_id,
                            'token': token,
                            'subclient_id': subclient},
                      token=token,
                      expected_status=expected_code)
        # print(f'Subclient token revocation: {r.text}')
        if expected_status == 'success':
            resp = r.json()
            self.assertEqual(expected_status, resp['status'], f'response: {r.text}')

    def test_identify(self):
        ident_data = self.do_identify()
        self.assertTrue(ident_data['user_id'], 'Expected a non-zero user ID')
        print()
        input(f"Please check that your user ID is {ident_data['user_id']} and press ENTER")

        # Now we should be able to use this access token.
        token = ident_data['oauth_token']['access_token']

        self.do_validate(token)

        # Expiration date should be in the future.
        now = datetime.datetime.now(tz=pytz.utc)
        expires = dateutil.parser.parse(ident_data['oauth_token']['expires'])
        self.assertGreater(expires, now)

    def test_logout(self):
        ident_data = self.do_identify()
        token = ident_data['oauth_token']['access_token']
        self.do_validate(token)

        # After logging out, validation should fail.
        self.do_logout(ident_data['user_id'], token)
        self.do_validate(token, expected_status='fail')

    def test_subclient_token(self):
        ident_data = self.do_identify()
        token = ident_data['oauth_token']['access_token']

        subtoken_info = self.do_create_subclient_token(token)

        # Expiration date should be in the future.
        now = datetime.datetime.now(tz=pytz.utc)
        expires = dateutil.parser.parse(subtoken_info['expires'])
        self.assertGreater(expires, now)

        # We shouldn't be able to use it directly as token.
        self.do_validate(subtoken_info['token'], expected_status='fail')

        # But as a subclient token it should be fine.
        self.do_validate(subtoken_info['token'], subclient=SUBCLIENT)

    def test_revoke_subclient_token(self):
        ident_data = self.do_identify()
        token = ident_data['oauth_token']['access_token']

        subtoken_info = self.do_create_subclient_token(token)
        self.do_validate(subtoken_info['token'], subclient=SUBCLIENT)

        # After revoking, it shouldn't work any more.
        self.do_revoke_subclient_token(ident_data['user_id'], subtoken_info['token'])
        self.do_validate(subtoken_info['token'], subclient=SUBCLIENT,
                         expected_status='fail')

        # Double-revoking shouldn't work either.
        self.do_revoke_subclient_token(ident_data['user_id'], subtoken_info['token'],
                                       expected_status='fail')

    def test_send_token_to_subclient(self):
        ident_data = self.do_identify()
        token = ident_data['oauth_token']['access_token']

        subtoken_info = self.do_create_subclient_token(token)
        self.do_validate(subtoken_info['token'], subclient=SUBCLIENT)

        r = self.post(urljoin(self.cloud_api, 'blender_id/store_scst'),
                      data={'user_id': ident_data['user_id'],
                            'subclient_id': SUBCLIENT,
                            'token': subtoken_info['token']})
        r.raise_for_status()

        # Let's check that the subclient token works now.
        self.get(urljoin(self.cloud_api, 'users/me'),
                 auth=(subtoken_info['token'], SUBCLIENT))
