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
5. Create super user ./manage.py createsuperuser
6. Load any fixtures you want to use.
   - list fixtures  `ls */fixtures/*`
   - `./manage.py loaddata blender_cloud_devserver`
   - `./manage.py loaddata default_site`
7. Run ./gulp  to compile javascript
8. Add to /etc/hosts  127.0.0.1 blender-id
9. ./manage.py runserver

## Setting up the Blender Store (and other `bid_api` users)

To allow the Blender Store to call our API endpoints, do the following:

- Add an OAuth2 application for the API, name it "Blender ID API". You can choose any name, but
  it's nice if we all use the same so we can recognise it. Set it to 'Confidential' and 'Resource
  owner password-based'.
- Make sure that the `cloud_demo` and `cloud_subscriber` roles exist, and that they are badges.
  Add a role `cloud_badger` and allow it to manage the above roles.
- Add a user for the Blender Store, for example using "yourname+store@yourdomain.com" as email
  address. The password doesn't matter -- give it a long one and forget about it. Give the user the
  `cloud_badger` role.
- Add an OAuth2 token to the Blender Store user for the Blender ID API application. Make sure it
  doesn't expire any time soon (e.g. somewhere in the year 2999). Give it the scopes
  `badger` and `usercreate`.
- Configure the Blender Store to use this token to authenticate its API calls.


## TODO

1. Check out the [default management
   endpoints](https://django-oauth-toolkit.readthedocs.io/en/latest/tutorial/tutorial_02.html#make-your-api)
   of the Django OAuth Toolkit.


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

Users with an invalid email address (based on format and length) are skipped. Note that migrating of
user-roles and user-settings will cause warnings; some users are skipped

The following tables are explicitly *not* migrated:
- collections
- cloud_membership
- cloud_subscription
- gooseberry_pledge
- mail_queue
- mail_queue_prepaid
- mail_queue_recurring
- users_collections


## Deployment notes

Assuming deployment on FreeBSD with uWSGI, take care to:

- Install `python36`, `apache24`, `a24_mod_proxy_uwsgi`, and `mysql56-server`.
- Add the following to `/etc/make.conf`. Remove the `.if` and `.endif` lines if you're fine having
  Python 3.6 as a global default.

      .if ${.CURDIR:M*/www/uwsgi*}
      DEFAULT_VERSIONS=python=3.6 python3=3.6
      .endif

- Build and install the `www/uwsgi` port and run `make clean`.
- Add the `uwsgi` user to the `www` group, or graceful restarts won't work due to permission
  problems. uWSGI tries to change ownership of `/tmp/uwsgi.sock` to `uwsgi:www`, and not being in
  the `www` group this would fail.
- Use the following file in `/usr/local/etc/uwsgi/uwsgi.ini`:

      [uwsgi]
      master = true
      enable-threads = true
      processes = 2
      virtualenv = /data/www/vhosts/www.blender.org/venv-bid/
      chdir = /data/www/vhosts/www.blender.org/blender-id/
      wsgi-file = /data/www/vhosts/www.blender.org/blender-id/blenderid/wsgi.py
      touch-reload = /data/www/vhosts/www.blender.org/blender-id/blenderid/wsgi.py

- Enable the following Apache modules:

      LoadModule proxy_module libexec/apache24/mod_proxy.so
      LoadModule proxy_uwsgi_module libexec/apache24/mod_proxy_uwsgi.so

- Use the following configuration for Apache, I placed it in `Includes/uwsgi.conf`:

      Alias /id/static/ /data/www/vhosts/www.blender.org/blender-id/static/
      <Directory /data/www/vhosts/www.blender.org/blender-id/static/>
          Require all granted
      </Directory>

      ProxyPass /id/static/ "!"
      ProxyPass /id unix:/tmp/uwsgi.sock|uwsgi://blender-id/
      ProxyPassReverse /id "www.blender.org/id/"

- Enable the required services in `/etc/rc.conf`:

      mysql_enable="YES"
      uwsgi_enable="YES"
      apache24_enable="YES"

      # Appears to not honour the configfile flag, pass as --ini instead
      # -- troubled/sybren @ Nov 21 2017 hangout chat
      #uwsgi_configfile="/usr/local/etc/uwsgi/uwsgi.ini"
      uwsgi_flags="-L --ini /usr/local/etc/uwsgi/uwsgi.conf"


## Troubleshooting

### "Site matching query does not exist."

Do this:

    ./manage.py loaddata default_site

Then access your site at http://blender-id:8000/. Add an entry to your hosts file if necessary.
