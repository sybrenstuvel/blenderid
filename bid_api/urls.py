from django.conf.urls import url

from .views import info, badger, create_user, authenticate

urlpatterns = [
    url(r'^(?:user|me)$', info.user_info, name='user'),
    url(r'^badger/grant/(?P<badge>[^/]+)/(?P<email>[^/]+)$',
        badger.BadgerView.as_view(action='grant'), name='badger_grant'),
    url(r'^badger/revoke/(?P<badge>[^/]+)/(?P<email>[^/]+)$',
        badger.BadgerView.as_view(action='revoke'), name='badger_revoke'),
    url(r'^check-user/(?P<email>[^/]+)$', create_user.CheckUserView.as_view(), name='check_user'),
    url(r'^create-user/?$', create_user.CreateUserView.as_view(), name='create_user'),
    url(r'^authenticate/?$', authenticate.AuthenticateView.as_view(), name='authenticate'),
]
