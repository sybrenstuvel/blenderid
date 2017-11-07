import os
import unittest

import requests


class AbstractBlenderIDTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = requests.Session()
        cls.endpoint = os.environ.get('BLENDER_ID_ENDPOINT')
        cls.assertTrue(cls.endpoint, 'Set the BLENDER_ID_ENDPOINT environment variable')

    def request(self, method: str, path: str, *,
                expected_status=200,
                token=None,
                etag=None,
                headers=None,
                **kwargs) -> requests.Response:

        from urllib.parse import urljoin

        if headers is None:
            headers = {}

        if etag is not None:
            if method in {'PUT', 'PATCH', 'DELETE'}:
                headers['If-Match'] = etag
            elif method == 'GET':
                headers['If-None-Match'] = etag
            else:
                raise ValueError(f'Not sure what to do with etag and method {method}')

        if token is not None:
            headers['Authorization'] = f'Bearer {token}'

        kwargs.setdefault('verify', True)

        url = urljoin(self.endpoint, path)
        resp = self.session.request(method, url, headers=headers, **kwargs)

        self.assertEqual(
            expected_status, resp.status_code,
            f'Expected status {expected_status} but got {resp.status_code}. Response: {resp.text}')

        return resp

    def get(self, *args, **kwargs):
        return self.request('GET', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request('POST', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request('PUT', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request('DELETE', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request('PATCH', *args, **kwargs)
