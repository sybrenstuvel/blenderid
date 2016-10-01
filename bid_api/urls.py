from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?:user|me)$', views.user_info, name='user'),
]
