"""
Assumes the old database tables have been loaded into the same database as the new.
"""

from collections import namedtuple

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.contrib.auth import get_user_model

from bid_main import models


def normalise_name(name):
    if name is None:
        return ''
    return name.strip()


def query(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        desc = cursor.description
        nt_result = namedtuple('Result', [col[0] for col in desc])

        for row in cursor.fetchall():
            result = nt_result(*row)
            yield result


class Command(BaseCommand):
    help = 'Migrates old BlenderID databases to the new structure'

    def add_arguments(self, parser):
        parser.add_argument('-k', '--keep-old-tables', action='store_true', default=False)

    @transaction.atomic()
    def handle(self, *args, **options):
        self.stdout.write('Migrating old DB to new.')

        self.migrate_users(*args, **options)

    def migrate_users(self, *args, **options):
        self.stdout.write('Migrating users.')

        migrated = skipped = 0
        user_cls = get_user_model()

        for result in query("SELECT * FROM user"):
            self.stdout.write('    - %s' % result.email, ending='')

            if len(result.email) > 64:
                # These are suspected to be invalid; at the time of writing there are
                # only 3 of those, those are 180+ characters long, and corrupted.
                self.stdout.write(self.style.NOTICE(' [skipped for invalid address]                '))
                skipped += 1
                continue

            try:
                user_cls.objects.get(email=result.email)
            except user_cls.DoesNotExist:
                pass
            else:
                self.stdout.write(self.style.NOTICE(' [skipped; exists]                          '))
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
                                last_login=result.last_login_at,
                                confirmed_email_at=result.confirmed_at,
                                last_login_ip=result.last_login_ip,
                                current_login_ip=result.current_login_ip,
                                login_count=result.login_count or 0)
            existing.save()

            # TODO: port settings and addresses

            migrated += 1
            self.stdout.write(self.style.SUCCESS(' [migrated]') + '                             ', ending='\r')

        if migrated:
            style = self.style.SUCCESS
        else:
            style = self.style.NOTICE
        self.stdout.write('')
        self.stdout.write(style('Migrated %i users, skipped %i' % (migrated, skipped)))
