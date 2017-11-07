import unittest


class CanaryTest(unittest.TestCase):
    def test_python_version(self):
        import sys

        if sys.version_info < (3, 6):
            self.fail('Python 3.6+ required, running %s' % sys.version)

    def test_server_known(self):
        import os
        import requests

        self.assertIn('BLENDER_ID_ENDPOINT', os.environ,
                      'Set the BLENDER_ID_ENDPOINT environment variable')

        endpoint = os.environ.get('BLENDER_ID_ENDPOINT')
        self.assertTrue(endpoint, 'Set the BLENDER_ID_ENDPOINT environment variable')

        username = os.environ.get('BLENDER_ID_UNAME')
        self.assertTrue(username, 'Set the BLENDER_ID_UNAME environment variable '
                                  'to your Blender ID login name')

        try:
            resp = requests.get(endpoint)
        except (IOError, OSError, requests.RequestException) as ex:
            self.fail(f'Unable to connect to {endpoint}: {ex}')
        self.assertEqual(200, resp.status_code)
