from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^about$', views.about, name='about'),
    url(r'^login$', views.about, name='login'),
    url(r'^logout$', views.about, name='logout'),
    url(r'^profile$', views.about, name='profile'),
]
