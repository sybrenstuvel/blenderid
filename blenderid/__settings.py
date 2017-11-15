"""
Local development settings.

Copy to settings.py and edit to suit your needs.
"""

# noinspection PyUnresolvedReferences
from blenderid.common_settings import *

DEBUG = True
BLENDER_ID_ADDON_CLIENT_ID = 'SPECIAL-SNOWFLAKE-57'

# Update this to something unique for your machine.
# This was generated using "pwgen -sync 64"
SECRET_KEY = r'''}y\[.~WGh2#~|6r|alD0R6<'WA@F#hB|4eyR\6SUyovx5H,v4TP#H~6unZGIgk~`'''

# For testing purposes, allow HTTP as well as HTTPS. Never enable this in production!
# OAUTH2_PROVIDER['ALLOWED_REDIRECT_URI_SCHEMES'] = ['http', 'https']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'blender_id_new',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': str(BASE_DIR / 'db.sqlite3'),
    # },
}


LOGGING = {
    'version': 1,
    'formatters': {
        'default': {'format': '%(asctime)-15s %(levelname)8s %(name)s %(message)s'}
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stderr',
        }
    },
    'loggers': {
        'bid_main': {'level': 'DEBUG'},
        'blenderid': {'level': 'DEBUG'},
        'bid_api': {'level': 'DEBUG'},
        'bid_addon_support': {'level': 'DEBUG'},
    },
    'root': {
        'level': 'WARNING',
        'handlers': [
            'console',
        ],
    }
}

# For Debug Toolbar, extend with whatever address you use to connect
# to your dev server.
INTERNAL_IPS = ['127.0.0.1']


# Don't use this in production, but only in tests.
# ALLOWED_HOSTS = ['*']
