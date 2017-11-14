import pprint
import webbrowser
from urllib.parse import urlencode

from abstract_bid_test import AbstractBlenderIDTest
import callbackserver

HTTP_PORTNR = 8666


class OAuthFlowTest(AbstractBlenderIDTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.auth_http_server: callbackserver.OAuthTokenHTTPServer = None
        self.access_token = ''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        import os

        cls.oauth_client_id = os.environ.get('BLENDER_ID_OAUTH_CLIENT', 'INTEGRATION-TESTS')
        cls.oauth_secret = os.environ.get('BLENDER_ID_OAUTH_SECRET')

        if not cls.oauth_secret or not cls.oauth_secret:
            raise ValueError('Set BLENDER_ID_OAUTH_CLIENT and BLENDER_ID_OAUTH_SECRET '
                             'environment variables')

        cls.oauth_authorize_url = cls.urljoin('oauth/authorize')

    def setUp(self):
        super().setUp()
        if self.access_token:
            return
        self.do_login()

    def tearDown(self):
        super().tearDown()
        self._stop_http_server()

    def _start_http_server(self):
        """Starts the HTTP server, if it wasn't started already."""

        if self.auth_http_server is not None:
            return
        self.auth_http_server = callbackserver.OAuthTokenHTTPServer(portnr=HTTP_PORTNR)

    def _stop_http_server(self):
        """Stops the HTTP server, if one was started."""

        if self.auth_http_server is None:
            return
        self.auth_http_server.server_close()
        self.auth_http_server = None

    def do_login(self):
        self._start_http_server()

        url = self.get_authorize_url()
        print(f'sending browser to {url}')

        webbrowser.open_new_tab(url)
        grant = self.auth_http_server.wait_for_oauth_grant()
        print(f'grant received: {grant}')
        self.assertIsNotNone(grant, "expected a grant, but didn't get one")

        # Trade for an auth token
        print('trading grant for an oauth token')
        r = self.post('oauth/token', data={
            'client_id': self.oauth_client_id,
            'client_secret': self.oauth_secret,
            'code': grant,
            'grant_type': 'authorization_code',
            'redirect_uri': self.get_callback_url()
        })
        print('reading response JSON')
        # Will be something like: {
        #     "access_token": "1jsW8bEiCx8vDfgP3muN6O87f59dEX",
        #     "token_type": "Bearer",
        #     "refresh_token": "34E9dPZSpivimpDLnyrShq20qg1MLt",
        #     "scope": "email"}
        resp = r.json()
        print(f'oauth/token response: {resp}')

        self.assertEqual('Bearer', resp['token_type'])
        self.access_token = resp['access_token']

    def do_revoke_token(self):
        self.assertTrue(self.access_token, 'need an access token to revoke')
        self.post('oauth/revoke',
                  auth=(self.oauth_client_id, self.oauth_secret),
                  allow_redirects=False,  # Refuse to be redirected to the login page
                  data={
                      'token': self.access_token,
                      'token_type_hint': 'access_token',
                  })

    def get_callback_url(self) -> str:
        return f'http://localhost:{HTTP_PORTNR}/'

    def get_authorize_url(self, **params: dict) -> str:
        """
        Returns a formatted authorize URL.

        :param params: Additional keyworded arguments to be added to the
            URL querystring.
        """

        params.update({
            'client_id': self.oauth_client_id,
            'response_type': 'code',
        })
        params.setdefault('scope', 'email')
        params.setdefault('redirect_uri', self.get_callback_url())

        return self.oauth_authorize_url + '?' + urlencode(params)

    def test_login_via_browser(self):
        # Check that we can use the access token
        r = self.get('api/user', token=self.access_token)
        my_info = r.json()

        print()
        print(f'My info:')
        pprint.pprint(my_info)
        input('Please verify the above info, and press ENTER if correct.')

    def test_revoke_token(self):
        self.get('api/user', token=self.access_token)
        self.do_revoke_token()

        # This token shouldn't work any more now.
        # Old Blender ID returns 401, this one returns 403.
        self.get('api/user', token=self.access_token, expected_status={401, 403})
