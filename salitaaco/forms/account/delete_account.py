from django import forms
from django.contrib.auth.models import User

from salitaaco.defaults.administrator_roles import ADMINISTRATOR
from salitaaco.utils.perms_check import is_administrator

from ..helpers import BaseForm


class DeleteAccountForm(BaseForm):
    password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "input",
            "id": "deleteAccountPassword",
            "autocomplete": "current-password",
            "placeholder": "Ilagay ang password",
        }),
        error_messages={"required": "Ilagay ang password para kumpirmahin."},
        label="Password",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("Maling password.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        # A guardian's children would be left with nobody to manage them, and
        # their pictures and recordings would stay behind, so they go first.
        guardian_account = getattr(self.user, "guardian_account", None)
        if guardian_account is not None and guardian_account.children.exists():
            raise forms.ValidationError(
                "May mga account ng bata pa sa ilalim mo. Burahin muna ang mga iyon sa pahinang Mga Bata."
            )
        # Without an admin nobody could run the site, or make a new admin in the app.
        if is_administrator(self.user) and not User.objects.filter(groups__name=ADMINISTRATOR).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError(
                "Ikaw ang nag-iisang admin. Gumawa muna ng isa pang admin sa Access control bago burahin ang account mo."
            )
        return cleaned_data
