Blender ID
==========

Test implementation of [Blender ID](https://www.blender.org/id/) using Django.

Requires Python 3.6, Django 1.10 and Django-OAuth-Toolkit.


## Post-clone configuration

Copy `blenderid/__settings.py` to `blenderid/settings.py` and adjust for your needs.

Run `git submodule update`


## Todo

1. Test against the Blender-ID Addon.
2. Test against Blender Cloud.
3. Port templates & assets from existing Blender ID.
4. Test against other websites using Blender ID
5. Deploy!


## Missing features

Subclients


# Including shared assets

`git submodule add git://git.blender.org/blender-web-assets.git static/assets_shared`
`git submodule init`
`git submodule update`
