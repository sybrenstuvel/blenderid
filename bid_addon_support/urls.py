from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^identify$', views.VerifyIdentityView.as_view(), name='identify'),
    url(r'^delete_token$', views.DeleteTokenView.as_view(), name='delete_token'),
    url(r'^validate_token$', views.ValidateTokenView.as_view(), name='validate_token'),
]
