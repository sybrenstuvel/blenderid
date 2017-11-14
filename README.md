# Blender ID

Test implementation of [Blender ID](https://www.blender.org/id/) using Django.

Requires Python 3.6, Django 1.11,
[Django-OAuth-Toolkit](https://django-oauth-toolkit.readthedocs.io/), and a database.


## Python Modules

The project contains the following top-level Python modules:

- `blenderid`: the Django project, includes all the settings and top-level URL config.
- `bid_main`: the main Django app, taking care of the web interface and OAuth2 authentication.
- `bid_addon_support`: Django app for the Blender ID add-on API, also known as "special snowflake
  authentication" (see below).
- `bid_api`: Django app for APIs that are neither OAuth2 nor Blender ID add-on support.


## Post-clone configuration

After cloning the Git repo, perform these steps to create a working dev server:

1. Copy `blenderid/__settings.py` to `blenderid/settings.py` and adjust for your needs.
2. Run `git submodule init` and `git submodule update`
3. Run `./manage.py migrate` to migrate your database to the latest version.
4. In production, set up a cron job that calls the
   [cleartokens](https://django-oauth-toolkit.readthedocs.io/en/latest/management_commands.html#cleartokens)
   management command regularly.


## TODO

1. Test against the Blender-ID Addon.
2. Test against Blender Cloud.
3. Port templates & assets from existing Blender ID.
4. Test against other websites using Blender ID
5. Check out the [default management
   endpoints](https://django-oauth-toolkit.readthedocs.io/en/latest/tutorial/tutorial_02.html#make-your-api)
   of the Django OAuth Toolkit.
5. Deploy!


## Blender ID add-on support

The Blender ID add-on specific authentication module basically provides a slight less secure but
more convenient way to obtain an OAuth authentication token. Effectively it allows username/password
entry in the application itself, rather than spawning a web browser.


## Differences with previous Blender ID

Even though we have tried to keep the API the same, there are a few subtle differences between this
Blender ID and the previous (Flask-based) incarnation:

- Date/times in JSON responses are encoded in ISO-8601 format (old used RFC-1123 with a hardcoded
  'GMT' timezone). ISO-8601 is the default format used by Django in all JSON responses, and, since it
  is also actually compatible with JavaScript, we decided to keep it. We suggest using
  [dateutil](https://dateutil.readthedocs.io/en/stable/) in Python projects to parse the timestamp.
  As it auto-detects the format, it can be used to transparently switch between the old and this
  Blender ID.
- Anonymous requests to a protected endpoint return a `403 Forbidden` response (old used `401
  Unauthorized`). This is the default Django behaviour.


## Migrating database from old to this Blender ID

The old Blender ID database can be migrated to the current one. This does require you to run MySQL
as the database.

1. Make sure you have a fresh `blender_id_new` MySQL database.
2. Load a backup of the old database into the current database, like `bzcat
   blender-id-backup-2017-11-14-1107.sql.bz2 | mysql blender_id_new`.
3. Create the current database structure using `manage.py migrate`.
4. Migrate the old data to the new structure using `manage.py migrate_olddb`.
5. Make yourself a super-user with `manage.py makesuperuser your.email@example.com`
6. After testing that everything works, remove the old data using `manage.py drop_olddb`.

Users with an invalid email address (based on format and length) are skipped. Note that migrating of user-roles and user-settings will cause warnings; some users are skipped

The following tables are explicitly *not* migrated:
- collections
- cloud_membership
- cloud_subscription
- gooseberry_pledge
- mail_queue
- mail_queue_prepaid
- mail_queue_recurring
- users_collections
