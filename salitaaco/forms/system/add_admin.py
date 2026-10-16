from django import forms
from django.contrib.auth.models import User

from salitaaco.utils.perms_check import is_administrator

from ..helpers import BaseForm


class AddAdminForm(BaseForm):
    """The username of an account that already exists, to give admin access to."""
    username = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={"class": "input", "autocomplete": "off", "placeholder": "username"}),
        error_messages={"required": "Ilagay ang username."},
        label="Username ng gagawing admin",
        help_text="Dapat may account na ang taong ito. Mananatili ang account niya bilang tagapag-alaga kung mayroon.",
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        self.user = User.objects.filter(username__iexact=username).first()
        if self.user is None:
            raise forms.ValidationError("Walang account na may ganitong username.")
        if is_administrator(self.user):
            raise forms.ValidationError("Admin na ang account na ito.")
        if not self.user.is_active:
            raise forms.ValidationError("Hindi aktibo ang account na ito.")
        return username
