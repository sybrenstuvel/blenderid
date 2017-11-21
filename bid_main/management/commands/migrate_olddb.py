"""
Assumes the old database tables have been loaded into the same database as the new.

The following tables are explicitly *not* migrated:

    - collections
    - cloud_membership
    - cloud_subscription
    - gooseberry_pledge
    - mail_queue
    - mail_queue_prepaid
    - mail_queue_recurring
    - users_collections

The migrate_olddb command is idempotent, i.e. it can be run multiple times
and it will gracefully skip already-migrated data.
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
        self.migrate_oauth_clients()
        self.migrate_oauth_tokens()

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
        self.stdout.write(self.style.SUCCESS('Migrated user-roles'))

    @transaction.atomic()
    def migrate_user_settings(self):
        with connection.cursor() as cursor:
            # "ignore" skips duplicates.
            cursor.execute('insert ignore into bid_main_usersetting (id, user_id, setting_id, unconstrained_value) '
                           'select id, user_id, setting_id, unconstrained_value from users_settings')
        self.stdout.write(self.style.SUCCESS('Migrated user-settings'))

    @transaction.atomic()
    def migrate_oauth_clients(self):
        from oauth2_provider.models import get_application_model
        from django.contrib.auth import get_user_model

        app_model = get_application_model()
        user_model = get_user_model()

        # Old database:
        # +---------------------------+------------------------------------------------------+--------------------------------------+------------------------------------------+-----------------------------------------------------+---------+--------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------------------------------+
        # | name                      | description                                          | picture                              | client_id                                | client_secret                                       | user_id | _redirect_uris                                                                                                                       | _default_scopes | url                                 |
        # +---------------------------+------------------------------------------------------+--------------------------------------+------------------------------------------+-----------------------------------------------------+---------+--------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------------------------------+
        # | Frameshift                | NULL                                                 | NULL                                 | asgiuehg90w09h4ingf8236yhfb9ijgtujdetghf | g4e6d78iujtf0vs9iuhws5rtfvrf9oiktg0okgghnpokjdfdsdf |   39055 | https://api.frameshift.studio/auth/login                                                                                             | email           | NULL                                |
        # | Blender Cloud             | Blender Cloud, by Blender Institute                  | blender_cloud.jpg                    | BLENDER-CLOUD-CLIENT                     | aerouthtcioiyrrorotenntzisnhatEa                    |       7 | https://cloud.blender.org/oauth/blender-id/authorized                                                                                | email           | NULL                                |
        # | Blender Conference        | The Blender event of the year.                       | fe4217352d0e73d7dee87ee8f93ad59c.jpg | BLENDER-CONFERENCE                       | asfkjhoigoeoihgoailjsagxcvaavvd                     |       7 | https://www.blender.org/conference/oauth/authorized http://www.blender.org/conference/oauth/authorized                               | email           | https://www.blender.org/conference  |
        # | Blender Conference DEV    | The Blender event of the year.                       | fe4217352d0e73d7dee87ee8f93ad59c.jpg | BLENDER-CONFERENCE-DEV                   | sosecret                                            |       7 | http://localhost:5000/oauth/authorized                                                                                               | email           | https://www.blender.org/conference  |
        # | Blender ID addon          | NULL                                                 | NULL                                 | BLENDER-ID-ADDON-CLIENT                  | aeaOEdrolopsJsDdanrnrnairarcmtnr                    |       7 |                                                                                                                                      | email           | NULL                                |
        # | Dalai Felinto             | Dalai's Adventures                                   | 2d94d846ba210a0e9c034194a666cdf6.jpg | DALAI-SECRET-ONLY                        | 8tNjZa0ZUHnwAY4fsaskjfh98yrh23jbkwfq98y3fh83        |    1522 | https://flask.dalaifelinto.com/callback/blender                                                                                      | email           | https://flask.dalaifelinto.com/     |
        # | Graphicall                | Bringing open source builds to the masses since 2005 | 88b4fe81313170a7e36bf607de816396.jpg | GRAPHICALL                               | graphicallsecred                                    |       7 | http://graphicall.org/login/                                                                                                         | email           | http://graphicall.org/about         |
        # | Rightclick Select         | NULL                                                 | NULL                                 | qkDocF9wc0Bc4pxnF3dcY4BJVa8up37A53TbbnmS | x23rqTg9r6izOQnl2UJEHbJ8DJgI8h6Y9AR33im3HB5bI8joci  |    8582 | https://rightclickselect.com/authorized                                                                                              | email           | http://rightclickselect.com/        |
        # | Blender Network Local     | Local blender network                                | NULL                                 | qkDocF9wc0Bc4pxnF3dcY4BJVa8up37QUdTMenmS | x23rqTg9r6izOQnl2UJEHbJ8DJgI8Wt0k3R33im3HB5bI8joci  |       7 | http://network.blender.org:5000/authorized                                                                                           | email           | NULL                                |
        # | Blender Today             | Community-driven Blender News                        | ab531849f8738e363eeaf089605ee999.png | sZ0fJCyYslqjWParf9exH5LMmToMXqESx92gu2dd | aVrmd0tXLwA3m6Mhlpsxc0DfOMUcRVkK6YL8Ngs5xFuCawS1fP  |       7 | http://blender.today/oauth/blender-id/authorized                                                                                     | email           | http://blender.today                |
        # | Blender Community         | Blender Community                                    | a04a5bce210bfb21251bd2f6af56b565.jpg | sZ0fJCyYslqjWParf9exH5LMmToMXqESx92gu2E6 | aVrmd0tXLwA3m6Mhlpsxc0DfOMUcRVkK6YL8Ngs5xFuCawS1fs  |       7 | https://blender.community/oauth/blender-id/authorized                                                                                | email           | https://blender.community           |
        # | Blender Network Staging   | The Blender Network website                          | ab531849f8738e363eeaf089605ee950.png | sZ0fJCyYslqjWParf9exH5LMmToMXqESx92gu2Ef | aVrmd0tXLwA3m6Mhlpsxc0DfOMUcRVkK6YL8Ngs5xFuCawS1fK  |       7 | https://staging.blendernetwork.org/authorized http://staging.blendernetwork.org/authorized https://www.blendernetwork.org/authorized | email           | https://www.blendernetwork.org      |
        # | Blender Network           | The Blender Network website                          | 451fd5e3aec35f94854112c0a0dbdd7d.png | sZ0fJCyYslqjWParf9exH5LMmToMXqESx92gu2Ej | aVrmd0tXLwA3m6Mhlpsxc0DfOMUcRVkK6YL8Ngs5xFuCawS1fP  |       7 | http://www.blendernetwork.org/authorized https://www.blendernetwork.org/authorized                                                   | email           | https://www.blendernetwork.org      |
        # | Blender Network Community | The Blender Network discussion platform              | 451fd5e3aec35f94854112c0a0dbdd7d.png | sZ0fJCyYslqjWParf9exH5LMmToMXqESx92gu2Es | aVrmd0tXLwA3m6Mhlpsxc0DfOMUcRVkK6YL8Ngs5xFuCawS1fs  |       7 | https://community.blendernetwork.org/oauth/blender-id/authorized                                                                     | email           | http://community.blendernetwork.org |
        # | HDRI Planet               | NULL                                                 | NULL                                 | u0XuWtbo7ahMl0FmA9FBCkilndLdlG9udRJmRRpA | hNhaHN9HDokKGTjOCSMR0UFeZc2NKnPzEjCGn6BG            |   29973 | http://hdriplanet.com/oauth/blender-id/auth                                                                                          | email           | http://hdriplanet.com               |
        # | HDRI Planet Local         | NULL                                                 | NULL                                 | x5ZPLQrMURtFnx801H0cyOg52H0cVSf2CHlEKnzX | vcRWSFbfoeGjabQo5NtlXFRgbQQQ7gE1zn24HDtF            |   29973 | http://hdriplanet.localhost/oauth/blender-id/auth                                                                                    | email           | http://hdriplanet.localhost         |
        # | Render Street             | Render Street                                        | NULL                                 | YspImpg18chyGZVzkhUwDdcfPiFynXQUIt003r7  | 8tNjZa0ZUHnwAY4m1wnmkMeRBhsqSnlCNHx8FFU             |   12322 | https://render.st/oauth/blender-id/auth                                                                                              | email           | https://render.st                   |
        # +---------------------------+------------------------------------------------------+--------------------------------------+------------------------------------------+-----------------------------------------------------+---------+--------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------------------------------+

        migrated = 0

        # Only query for clients that don't exist yet.
        for result in query("SELECT name, client_id, client_secret, _redirect_uris as redirect_uris, user_id, url FROM client WHERE client_id not in "
                            "(SELECT client_id FROM %s)" % app_model._meta.db_table):
            user = user_model.objects.get(id=result.user_id)
            is_bid_addon = result.client_id == 'BLENDER-ID-ADDON-CLIENT'

            app = app_model(
                authorization_grant_type='password' if is_bid_addon else 'authorization-code',
                client_id=result.client_id,
                client_secret=result.client_secret,
                client_type='confidential',
                name=result.name,
                redirect_uris=result.redirect_uris,
                skip_authorization=False,
                url=result.url or '',
                user=user,
            )
            app.save()
            migrated += 1

        self.stdout.write(self.style.SUCCESS('Migrated %d OAuth2 applications' % migrated))

    @transaction.atomic()
    def migrate_oauth_tokens(self):
        from oauth2_provider import models as oa2_models
        from django.contrib.auth import get_user_model

        app_model = oa2_models.get_application_model()
        at_model = oa2_models.get_access_token_model()
        rt_model = oa2_models.get_refresh_token_model()
        user_model = get_user_model()

        # Old database:
        # +---------------+--------------+------+-----+---------+----------------+
        # | Field         | Type         | Null | Key | Default | Extra          |
        # +---------------+--------------+------+-----+---------+----------------+
        # | id            | int(11)      | NO   | PRI | NULL    | auto_increment |
        # | client_id     | varchar(40)  | NO   | MUL | NULL    |                |
        # | user_id       | int(11)      | NO   | MUL | NULL    |                |
        # | token_type    | varchar(40)  | YES  |     | NULL    |                |
        # | access_token  | varchar(255) | YES  | UNI | NULL    |                |
        # | refresh_token | varchar(255) | YES  | UNI | NULL    |                |
        # | expires       | datetime     | YES  |     | NULL    |                |
        # | _scopes       | text         | YES  |     | NULL    |                |
        # | host_label    | varchar(255) | YES  |     | NULL    |                |
        # | subclient     | varchar(40)  | YES  |     | NULL    |                |
        # +---------------+--------------+------+-----+---------+----------------+

        migrated = 0

        # Get an in-memory maping from client ID to application.
        apps = {app.client_id: app for app in app_model.objects.all()}

        # Some optimisation to only fetch a user when it's different than the previous one.
        last_user = None
        skip_user_id = None

        # noinspection PyProtectedMember
        sql = (f"SELECT client_id, user_id, access_token, refresh_token, expires, "
               f"_scopes as scopes, host_label, subclient "
               f"FROM token "
               f"WHERE "
               f" expires > now() "
               f" and access_token  not in (select token from {at_model._meta.db_table}) "
               f" and refresh_token not in (select token from {rt_model._meta.db_table}) "
               f"ORDER BY user_id")

        for result in query(sql):

            # Some optimisation to only fetch a user when it's different than the previous one.
            if skip_user_id is not None:
                if result.user_id == skip_user_id:
                    continue
                # We've skipped that user, time to forget about it.
                skip_user_id = None

            if last_user is None or last_user.id != result.user_id:
                try:
                    user = user_model.objects.get(id=result.user_id)
                except user_model.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'User {result.user_id} does not exist, skipping tokens'))
                    skip_user_id = result.user_id
                    continue

                last_user = user
            else:
                user = last_user

            app = apps[result.client_id]

            at = at_model(
                user=user,
                token=result.access_token,
                application=app,
                expires=localise_datetime(result.expires),
                scope=result.scopes or '',
                host_label=result.host_label or '',
                subclient=result.subclient or '',
            )
            at.save()

            if result.refresh_token:
                rt = rt_model(
                    user=user,
                    token=result.refresh_token,
                    application=app,
                    access_token=at,
                )
                rt.save()

            migrated += 1

        self.stdout.write(self.style.SUCCESS('Migrated %d OAuth2 tokens' % migrated))
