from django import forms
from django.contrib.auth import forms as auth_forms
from .models import User


class BootstrapModelFormMixin:
    """Adds the Bootstrap CSS class 'form-control' to all form fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class UserRegistrationForm(BootstrapModelFormMixin, forms.ModelForm):
    # This class uses 'bid_main/user_register_form.html' to render
    class Meta:
        model = User
        fields = ['full_name', 'email', ]


class SetPasswordForm(BootstrapModelFormMixin, auth_forms.SetPasswordForm):
    pass
