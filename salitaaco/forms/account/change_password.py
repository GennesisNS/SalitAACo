from django import forms

from ..authentication import MIN_PASSWORD_LENGTH
from ..helpers import BaseForm


class ChangePasswordForm(BaseForm):
    current_password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "current-password", "placeholder": "••••••••"}),
        error_messages={"required": "Ilagay ang kasalukuyang password."},
        label="Kasalukuyang Password",
    )
    new_password = forms.CharField(
        required=True,
        strip=False,
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password", "placeholder": "min. 4 characters"}),
        error_messages={
            "required": "Ang bagong password ay dapat may hindi bababa sa 4 na character.",
            "min_length": "Ang bagong password ay dapat may hindi bababa sa 4 na character.",
        },
        label="Bagong Password (min. 4)",
    )
    confirm_password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password", "placeholder": "ulitin ang bago"}),
        error_messages={"required": "Hindi magkatugma ang bagong password at kumpirmasyon."},
        label="Kumpirmahin ang Bagong Password",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        current_password = self.cleaned_data["current_password"]
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Maling kasalukuyang password.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error("confirm_password", "Hindi magkatugma ang bagong password at kumpirmasyon.")
        return cleaned_data
