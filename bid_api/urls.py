from django.conf.urls import url

from .views import info, badger

urlpatterns = [
    url(r'^(?:user|me)$', info.user_info, name='user'),
    url(r'^badger/grant/(?P<badge>[^/]+)/(?P<email>[^/]+)$',
        badger.BadgerView.as_view(action='grant'), name='badger_grant'),
    url(r'^badger/revoke/(?P<badge>[^/]+)/(?P<email>[^/]+)$',
        badger.BadgerView.as_view(action='revoke'), name='badger_revoke'),
]
