"""
Drops the database tables used by the old Blender ID.

Assumes a previous 'manage.py migrate_olddb' command was given and tested properly.
"""

from collections import namedtuple

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.contrib.auth import get_user_model, models as auth_models
import pytz

from bid_main import models
from .migrate_olddb import query


class Command(BaseCommand):
    help = 'Drops the database tables used by the old Blender ID'

    def handle(self, *args, **options):
        self.stdout.write('Dropping old DB tables.')

        with connection.cursor() as cursor:
            for name in (
                    'alembic_version',
                    'users_settings',
                    'users_rest_tokens',
                    'setting',
                    'token',
                    'roles_users',
                    'grant',
                    'client',
                    'address',
                    'role',
                    'users_collections',
                    'collection',
                    'cloud_subscription',
                    'cloud_membership',
                    'gooseberry_pledge',
                    'mail_queue',
                    'mail_queue_prepaid',
                    'mail_queue_recurring',
                    'user',
            ):
                self.stdout.write(f'Dropping {name}')
                cursor.execute(f'drop table if exists `{name}`')
