"""
Password hasher that performs the same operations as Flask-Security.
"""

import base64
import hashlib
import hmac

from django.contrib.auth.hashers import BCryptPasswordHasher, mask_hash

_password_salt = b'/2aX16zPnnIgfMwkOjGX4S'


def get_hmac(password):
    h = hmac.new(_password_salt, password.encode('utf-8'), hashlib.sha512)
    return base64.b64encode(h.digest())


class BlenderIdPasswordHasher(BCryptPasswordHasher):
    algorithm = 'blenderid'

    def encode(self, password, salt):
        return super().encode(get_hmac(password), salt)

