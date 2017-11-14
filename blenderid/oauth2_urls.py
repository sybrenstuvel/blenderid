""""
New URL mapping to be compatible with Blender Cloud and other Blender ID users.

This mapping uses optional trailing slashes, and thus adheres better to RFC 6749.
I've also removed the "management" URLs, as we use the admin interface for that.
"""

from __future__ import absolute_import
from django.conf.urls import url

from oauth2_provider import views

urlpatterns = (
    url(r'^authorize/?$', views.AuthorizationView.as_view(), name="authorize"),
    url(r'^token/?$', views.TokenView.as_view(), name="token"),
    url(r'^revoke/?$', views.RevokeTokenView.as_view(), name="revoke-token"),
)
