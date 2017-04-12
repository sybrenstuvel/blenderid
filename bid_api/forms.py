"""
Forms for validating API calls.
"""

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import ugettext_lazy as _

UserModel = get_user_model()


class StoreAPICreateUserForm(forms.ModelForm):
    new_password = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput,
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )

    class Meta:
        model = UserModel
        fields = ['full_name', 'email', ]

    def clean_new_password(self):
        new_password = self.cleaned_data.get("new_password")
        self.instance.email = self.cleaned_data.get('email')
        password_validation.validate_password(new_password, self.instance)
        return new_password

    def save(self, commit=True):
        password = self.cleaned_data["new_password"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
