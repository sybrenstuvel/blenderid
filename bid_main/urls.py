from django.conf.urls import url
from .views import RegistrationView
from django.contrib.auth import views as auth_views

from . import views, forms

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^about$', views.about, name='about'),
    url(r'^login$', auth_views.login, {
        'template_name': 'login.html',
        'authentication_form': forms.AuthenticationForm,
    }, name='login'),
    url(r'^logout$', auth_views.logout, {
        'next_page': 'bid_main:about',
    }, name='logout'),
    url(r'^profile$', views.about, name='profile'),

    # Source of registration machinery: http://musings.tinbrain.net/blog/2014/sep/21/registration-django-easy-way/
    url(r'^register/$', RegistrationView.as_view(), name='register'),
    url(r'^register/signed-up/$', auth_views.password_reset_done, {
        'template_name': 'registration/initial_signed_up.html',
    }, name='register-done'),

    url(r'^register/password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, {
            'template_name': 'registration/initial_set_password.html',
            'post_reset_redirect': 'bid_main:register-complete',
            'set_password_form': forms.SetInitialPasswordForm,
        }, name='register-confirm'),
    url(r'^register/complete/$', auth_views.password_reset_complete, {
        'template_name': 'registration/registration_complete.html',
    }, name='register-complete'),

]
