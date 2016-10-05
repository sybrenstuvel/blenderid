"""
Assumes the old database tables have been loaded into the same database as the new.
"""


from collections import namedtuple

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.contrib.auth import get_user_model

from bid_main import models

class Command(BaseCommand):
    help = 'Migrates old BlenderID databases to the new structure'

    def add_arguments(self, parser):
        parser.add_argument('-k', '--keep-old-tables', action='store_true', default=False)

    def handle(self, *args, **options):
        self.stdout.write('Migrating old DB to new.')

        self.migrate_users(*args, **options)

    def migrate_users(self, *args, **options):
        self.stdout.write('Migrating users.')

        migrated = skipped = 0

        user_cls = get_user_model()

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user")
            desc = cursor.description
            nt_result = namedtuple('Result', [col[0] for col in desc])

            for row in cursor.fetchall():
                result = nt_result(*row)
                self.stdout.write('    - %s' % result.email, ending='')

                try:
                    user_cls.objects.get(email=result.email)
                except user_cls.DoesNotExist:
                    pass
                else:
                    self.stdout.write(self.style.NOTICE(' [skipped]'))
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
                existing = user_cls(username=result.email,
                                    password='blenderid$%s' % result.password,
                                    email=result.email,
                                    is_active=result.active,
                                    last_login=result.last_login_at)
                existing.save()

                # Port the profile
                existing.profile.full_name = result.full_name
                existing.profile.confirmed_email_at = result.confirmed_at
                existing.profile.last_login_ip = result.last_login_ip
                existing.profile.current_login_ip = result.current_login_ip
                existing.profile.login_count = result.login_count
                existing.profile.save()

                # TODO: port settings and addresses

                migrated += 1
                self.stdout.write(self.style.SUCCESS(' [migrated]'))

        if migrated:
            style = self.style.SUCCESS
        else:
            style = self.style.NOTICE
        self.stdout.write(style('Migrated %i users, skipped %i' % (migrated, skipped)))
