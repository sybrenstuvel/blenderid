import logging

from django import forms
from django.contrib.auth import forms as auth_forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .models import User

log = logging.getLogger(__name__)


class BootstrapModelFormMixin:
    """Adds the Bootstrap CSS class 'form-control' to all form fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        kwargs.setdefault('label_suffix', '')

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class UserRegistrationForm(BootstrapModelFormMixin, forms.ModelForm):
    # This class uses 'bid_main/user_register_form.html' to render
    class Meta:
        model = User
        fields = ['full_name', 'email', ]


class SetInitialPasswordForm(BootstrapModelFormMixin, auth_forms.SetPasswordForm):
    """Used when setting password in user registration flow.

    This means that the user has clicked on a link sent by email, so this
    confirms their email address.
    """

    def save(self, commit=True):
        self.user.confirmed_email_at = timezone.now()
        log.info('Confirmed email of %s throuhg initial password form.', self.user.email)

        return super().save(commit=commit)


class AuthenticationForm(BootstrapModelFormMixin, auth_forms.AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['placeholder'] = 'Your e-mail address'
        self.fields['password'].widget.attrs['placeholder'] = 'Your password'


class UserProfileForm(BootstrapModelFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name']

    def clean_full_name(self):
        full_name = self.cleaned_data['full_name'].strip()
        if not full_name:
            raise forms.ValidationError(_('Full Name is a required field'))
        return full_name


class PasswordChangeForm(BootstrapModelFormMixin, auth_forms.PasswordChangeForm):
    """Password change form with Bootstrap CSS classes."""


class AppRevokeTokensForm(forms.Form):
    """Form for revoking OAuth tokens for a specific application."""

    app_id = forms.IntegerField(widget=forms.HiddenInput)
