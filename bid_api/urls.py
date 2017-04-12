from django.conf.urls import url

from . import views, views_badger

urlpatterns = [
    url(r'^(?:user|me)$', views.user_info, name='user'),
    url(r'^badger/grant/(?P<badge>\w)/(?P<email>[^/]+)$', views_badger.badger_grant, name='badger_grant'),
    url(r'^badger/revoke/(?P<badge>\w)/(?P<email>[^/]+)$', views_badger.badger_revoke, name='badger_revoke'),
]
