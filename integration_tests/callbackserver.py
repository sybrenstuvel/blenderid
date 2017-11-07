"""Short-lived server for receiving OAuth callbacks.

Originally written for the Python FlickrAPI library, by Sybren A. Stüvel,
https://stuvel.eu/flickrapi
"""

import http.server
import logging
import urllib.parse

import callbackhtml


class OAuthTokenHTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # /?code=72157630789362986-5405f8542b549e95

        qs = urllib.parse.urlsplit(self.path).query
        url_vars = urllib.parse.parse_qs(qs)

        grant_code = url_vars['code'][0]

        self.server.grant_code = grant_code
        assert isinstance(self.server.grant_code, str)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.wfile.write(callbackhtml.auth_okay_html.encode('utf8'))


class OAuthTokenHTTPServer(http.server.HTTPServer):
    """HTTP server on a hardcoded port, which will receive the OAuth verifier."""

    def __init__(self, *, portnr: int):

        self.log = logging.getLogger('%s.%s' % (self.__class__.__module__, self.__class__.__name__))

        self.local_addr = ('127.0.0.1', portnr)
        self.allow_reuse_address = True
        self.log.info('Creating HTTP server at %s', self.local_addr)

        http.server.HTTPServer.__init__(self, self.local_addr, OAuthTokenHTTPHandler)

        self.grant_code = None

    def wait_for_oauth_grant(self, timeout=None):
        """Starts the HTTP server, waits for the OAuth grant."""

        if self.grant_code is None:
            self.timeout = timeout
            self.handle_request()

        if self.grant_code:
            self.log.info('OAuth verifier: %s' % self.grant_code)

        return self.grant_code

    @property
    def oauth_callback_url(self):
        return f'http://localhost:{self.local_addr[1]}/'
