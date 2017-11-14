import os
import typing
import unittest
from urllib.parse import urljoin

import requests


class AbstractBlenderIDTest(unittest.TestCase):
    endpoint: str = ''

    @classmethod
    def setUpClass(cls):
        from requests.adapters import HTTPAdapter
        cls.session = requests.Session()
        cls.session.mount('https://', HTTPAdapter(max_retries=5))
        cls.session.mount('http://', HTTPAdapter(max_retries=5))

        cls.endpoint = os.environ.get('BLENDER_ID_ENDPOINT')
        if not cls.endpoint:
            raise SystemExit('Set the BLENDER_ID_ENDPOINT environment variable')

    @classmethod
    def urljoin(cls, relative_url: str) -> str:
        return urljoin(cls.endpoint, relative_url)

    def request(self, method: str, path: str, *,
                expected_status: typing.Union[int, typing.Set[int]]=200,
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

        if isinstance(expected_status, int):
            expected_status = {expected_status}
        self.assertIn(
            resp.status_code, expected_status,
            f'Expected status {expected_status} but got {resp.status_code}. '
            f'Response: {resp.text[:300]}')

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
