from django.conf.urls import url

from .views import info, badger

urlpatterns = [
    url(r'^(?:user|me)$', info.user_info, name='user'),
    url(r'^badger/grant/(?P<badge>\w)/(?P<email>[^/]+)$', badger.badger_grant, name='badger_grant'),
    url(r'^badger/revoke/(?P<badge>\w)/(?P<email>[^/]+)$', badger.badger_revoke, name='badger_revoke'),
]
