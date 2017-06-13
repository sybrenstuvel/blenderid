Blender ID
==========

Test implementation of [Blender ID](https://www.blender.org/id/) using Django.

Requires Python 3.5, Django 1.9 and Django-OAuth-Toolkit. Upgrade to Django 1.10 will
be done as soon as Django-OAuth-Toolkit supports it.

## Post-clone configuration

Copy `blenderid/__settings.py` to `blenderid/settings.py` and adjust for your needs.

## Todo

1. Test against the Blender-ID Addon.
2. Test against Blender Cloud.
3. Port templates & assets from existing Blender ID.
4. Port to existing MySQL database (currently using SQLite).
5. Create settings_local.py override system.
6. Test against other websites using Blender ID
7. Deploy!

## Missing features

Subclients

# Including shared assets

`git submodule add git://git.blender.org/blender-web-assets.git static/assets_shared`
`git submodule init`
`git submodule update`
