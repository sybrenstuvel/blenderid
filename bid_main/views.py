from django.db import transaction
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.views.generic.edit import UpdateView

from .forms import UserRegistrationForm, UserProfileForm, AuthenticationForm
from .models import User


class PageIdTemplateView(TemplateView):
    page_id = ''

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_id'] = self.page_id


class IndexView(LoginRequiredMixin, PageIdTemplateView):
    template_name = 'index.html'
    page_id = 'index'
    login_url = reverse_lazy('bid_main:login')
    redirect_field_name = None


class RegistrationView(CreateView):
    form_class = UserRegistrationForm
    model = User
    template_name_suffix = '_register_form'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.set_password(User.objects.make_random_password())
        obj.save()

        # This form only requires the "email" field, so will validate.
        reset_form = PasswordResetForm(self.request.POST)
        reset_form.is_valid()  # Must trigger validation

        # Copied from django/contrib/auth/views.py : password_reset
        opts = {
            'use_https': self.request.is_secure(),
            'email_template_name': 'registration/email_verification.txt',
            'html_email_template_name': 'registration/email_verification.html',
            'subject_template_name': 'registration/email_verification_subject.txt',
            'request': self.request,
            # 'html_email_template_name': provide an HTML content template if you desire.
        }
        # This form sends the email on save()
        reset_form.save(**opts)

        return redirect('bid_main:register-done')


class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = UserProfileForm
    model = User
    template_name = 'settings/profile.html'
    success_url = reverse_lazy('bid_main:index')

    def get_object(self, queryset=None):
        return self.request.user


class SwitchUserView(LoginRequiredMixin, LoginView):
    template_name = 'switch_user.html'
    form_class = AuthenticationForm
    success_url_allowed_hosts = settings.NEXT_REDIR_AFTER_LOGIN_ALLOWED_HOSTS


def test_error(request, code):
    from django.core import exceptions
    from django.http import response, Http404

    codes = {
        403: exceptions.PermissionDenied,
        404: Http404,
        500: exceptions.ImproperlyConfigured,
    }
    try:
        exc = codes[int(code)]
    except KeyError:
        return response.HttpResponse(f'error test for code {code}', status=int(code))
    else:
        raise exc(f'exception test for code {code}')


class ErrorView(TemplateView):
    """Renders an error page."""
    # TODO(Sybren): respond as JSON when this is an XHR.

    status = 500

    def dispatch(self, request, *args, **kwargs):
        from django.http.response import HttpResponse
        if request.method in {'HEAD', 'OPTIONS'}:
            # Don't render templates in this case.
            return HttpResponse(status=self.status)

        # We allow any method for this view,
        response = self.render_to_response(self.get_context_data(**kwargs))
        response.status_code = self.status
        return response
