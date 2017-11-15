from django.conf.urls import url
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

from . import views, forms

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^about$',
        RedirectView.as_view(permanent=True, url=reverse_lazy('bid_main:login')),
        name='about'),
    url(r'^settings/profile$', views.ProfileView.as_view(), name='profile'),
    url(r'^login$',
        auth_views.LoginView.as_view(template_name='login.html',
                                     authentication_form=forms.AuthenticationForm),
        name='login'),
    url(r'^logout$', auth_views.LogoutView.as_view(next_page='bid_main:about'), name='logout'),
    url(r'^switch', views.SwitchUserView.as_view(), name='switch_user'),

    url('^change$',
        auth_views.PasswordChangeView.as_view(
            form_class=forms.PasswordChangeForm,
            success_url=reverse_lazy('bid_main:password_change_done')),
        name='password_change'),
    url('^change-password/done$', auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done'),

    url(r'^password_reset/$',
        auth_views.PasswordResetView.as_view(
            success_url=reverse_lazy('bid_main:password_reset_done')),
        name='password_reset'),
    url(r'^password_reset/done/$',
        auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$$',
        auth_views.PasswordResetConfirmView.as_view(
            success_url=reverse_lazy('bid_main:password_reset_complete')),
        name='password_reset_confirm'),
    url(r'^password_reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),

    # Source of registration machinery:
    # http://musings.tinbrain.net/blog/2014/sep/21/registration-django-easy-way/
    url(r'^register/$', views.RegistrationView.as_view(), name='register'),
    url(r'^register/signed-up/$',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/initial_signed_up.html'),
        name='register-done'),
    url(
        r'^register/password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, {
            'template_name': 'registration/initial_set_password.html',
            'post_reset_redirect': 'bid_main:register-complete',
            'set_password_form': forms.SetInitialPasswordForm,
        }, name='register-confirm'),
    url(r'^register/complete/$', auth_views.password_reset_complete, {
        'template_name': 'registration/registration_complete.html',
    }, name='register-complete'),

    # Only enable this on a dev server:
    # url(r'^error/(?P<code>\d+)$', views.test_error)
]
