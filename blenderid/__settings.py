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
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '%(asctime)-15s %(levelname)8s %(name)s %(message)s'
        },
        'verbose': {
            'format': '%(asctime)-15s %(levelname)8s %(name)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',  # Set to 'verbose' in production
            'stream': 'ext://sys.stderr',
        },
        # Enable this in production:
        # 'sentry': {
        #     'level': 'ERROR',  # To capture more than ERROR, change to WARNING, INFO, etc.
        #     'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        #     # 'tags': {'custom-tag': 'x'},
        # },
    },
    'loggers': {
        'bid_main': {'level': 'DEBUG'},
        'blenderid': {'level': 'DEBUG'},
        'bid_api': {'level': 'DEBUG'},
        'bid_addon_support': {'level': 'DEBUG'},
        'sentry.errors': {'level': 'DEBUG', 'handlers': ['console'], 'propagate': False},
    },
    'root': {
        'level': 'WARNING',
        'handlers': [
            'console',
            # Enable this in production:
            # 'sentry',
        ],
    }
}

# For Debug Toolbar, extend with whatever address you use to connect
# to your dev server.
INTERNAL_IPS = ['127.0.0.1']


# Don't use this in production, but only in tests.
# ALLOWED_HOSTS = ['*']


# # Raven is the Sentry.io integration app for Django. Enable this on production:
# import os
# import raven
# INSTALLED_APPS.append('raven.contrib.django.raven_compat')
#
# RAVEN_CONFIG = {
#     'dsn': 'https://<key>:<secret>@sentry.io/<project>',
#     # If you are using git, you can also automatically configure the
#     # release based on the git info.
#     'release': raven.fetch_git_sha(os.path.abspath(os.curdir)),
# }
