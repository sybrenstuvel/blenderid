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
5. Check out the
5. Deploy!


## Blender ID add-on support

The Blender ID add-on specific authentication module basically provides a slight less secure but
more convenient way to obtain an OAuth authentication token. Effectively it allows username/password
entry in the application itself, rather than spawning a web browser.


# Including shared assets

    git submodule add git://git.blender.org/blender-web-assets.git static/assets_shared
    git submodule init
    git submodule update
