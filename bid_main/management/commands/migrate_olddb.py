"""
Assumes the old database tables have been loaded into the same database as the new.
"""

from collections import namedtuple

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.contrib.auth import get_user_model, models as auth_models
import pytz

from bid_main import models


def normalise_name(name):
    if name is None:
        return ''
    return name.strip()


def query(sql, args=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, args)
        desc = cursor.description
        nt_result = namedtuple('Result', [col[0] for col in desc])

        for row in cursor.fetchall():
            result = nt_result(*row)
            yield result


def localise_datetime(dt):
    """The datetimes in the old database were in UTC, without explicit timezone."""

    if dt is None:
        return None
    return pytz.timezone('UTC').localize(dt)


class Command(BaseCommand):
    help = 'Migrates old BlenderID databases to the new structure'

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)
        self.name_to_role = {}

    def handle(self, *args, **options):
        self.stdout.write('Migrating old DB to new.')

        self.migrate_roles()
        self.migrate_settings()
        self.migrate_users(*args, **options)
        self.migrate_user_roles()
        self.migrate_user_settings()

    @transaction.atomic()
    def migrate_roles(self):
        self.stdout.write('Migrating roles.')

        for result in query("SELECT * FROM role"):
            self.stdout.write('    - %s' % result.name)

            try:
                role = models.Role.objects.get(name=result.name)
            except models.Role.DoesNotExist:
                descr = result.description or ''
                is_active = True

                if descr == 'INACTIVE':
                    descr = ''
                    is_active = False

                role = models.Role(id=result.id, name=result.name,
                                   description=descr,
                                   is_active=is_active)
                role.save()

            self.name_to_role[result.name] = role
        self.stdout.write(self.style.SUCCESS('Migrated %i roles') % len(self.name_to_role))

    @transaction.atomic()
    def migrate_settings(self):
        self.stdout.write('Migrating settings.')

        with connection.cursor() as cursor:
            # "ignore" skips duplicates.
            cursor.execute('insert ignore into bid_main_setting (id, name, description, data_type, `default`) '
                           'select id, name, description, data_type, `default` from setting')

    @transaction.atomic()
    def migrate_users(self, *args, **options):
        self.stdout.write('Migrating users.')

        migrated = skipped = 0
        user_cls = get_user_model()

        # Only query for users that don't exist yet.
        for result in query("SELECT * FROM user where email not in (select email from bid_main_user)"):

            if len(result.email) > 64:
                # These are suspected to be invalid; at the time of writing there are
                # only 3 of those, those are 180+ characters long, and corrupted.
                self.stdout.write('    - %s %s' % (result.email, self.style.NOTICE(' [skipped for invalid address]')))
                skipped += 1
                continue

            try:
                user_cls.objects.get(email=result.email)
            except user_cls.DoesNotExist:
                pass
            else:
                self.stdout.write('    - %s %s' % (result.email, self.style.NOTICE(' [skipped; exists]')))
                skipped += 1
                continue

            # +------------------+--------------+------+-----+---------+----------------+
            # | Field            | Type         | Null | Key | Default | Extra          |
            # +------------------+--------------+------+-----+---------+----------------+
            # | id               | int(11)      | NO   | PRI | NULL    | auto_increment |
            # | email            | varchar(255) | YES  | UNI | NULL    |                |
            # | password         | varchar(255) | YES  |     | NULL    |                |
            # | active           | tinyint(1)   | YES  |     | NULL    |                |
            # | confirmed_at     | datetime     | YES  |     | NULL    |                |
            # | braintree_id     | varchar(255) | YES  |     | NULL    |                |
            # | paypal_id        | varchar(64)  | YES  |     | NULL    |                |
            # | first_name       | varchar(255) | YES  |     | NULL    |                |
            # | last_name        | varchar(255) | YES  |     | NULL    |                |
            # | last_login_at    | datetime     | YES  |     | NULL    |                |
            # | current_login_at | datetime     | YES  |     | NULL    |                |
            # | last_login_ip    | varchar(100) | YES  |     | NULL    |                |
            # | current_login_ip | varchar(100) | YES  |     | NULL    |                |
            # | login_count      | int(11)      | YES  |     | NULL    |                |
            # | full_name        | varchar(255) | YES  |     | NULL    |                |
            # +------------------+--------------+------+-----+---------+----------------+

            # Port the user
            existing = user_cls(id=result.id,
                                email=result.email,
                                password='blenderid$%s' % result.password,
                                full_name=normalise_name(result.full_name),
                                is_active=bool(result.active),
                                last_login=localise_datetime(result.last_login_at),
                                confirmed_email_at=localise_datetime(result.confirmed_at),
                                last_login_ip=result.last_login_ip,
                                current_login_ip=result.current_login_ip,
                                login_count=result.login_count or 0)
            existing.save()
            migrated += 1

        if migrated:
            style = self.style.SUCCESS
        else:
            style = self.style.NOTICE
        self.stdout.write('')
        self.stdout.write(style('Migrated %i users, skipped %i' % (migrated, skipped)))

    @transaction.atomic()
    def migrate_user_roles(self):
        with connection.cursor() as cursor:
            # "ignore" skips duplicates.
            cursor.execute('insert ignore into bid_main_user_roles (user_id, role_id) '
                           'select user_id, role_id from roles_users')

    @transaction.atomic()
    def migrate_user_settings(self):
        with connection.cursor() as cursor:
            # "ignore" skips duplicates.
            cursor.execute('insert ignore into bid_main_usersetting (id, user_id, setting_id, unconstrained_value) '
                           'select id, user_id, setting_id, unconstrained_value from users_settings')
