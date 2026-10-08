from django import forms

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
        return cleaned_data
