from django import forms

from ..helpers import BaseForm


class DeleteChildForm(BaseForm):
    """Deleting a child's account is confirmed with the guardian's own password."""
    password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "input",
            "id": "deleteChildPassword",
            "autocomplete": "current-password",
            "placeholder": "Ilagay ang password mo",
        }),
        error_messages={"required": "Ilagay ang password mo para kumpirmahin."},
        label="Password mo",
    )

    def __init__(self, *args, guardian_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.guardian_user = guardian_user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.guardian_user.check_password(password):
            raise forms.ValidationError("Maling password.")
        return password
