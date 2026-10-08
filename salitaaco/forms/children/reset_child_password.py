from django import forms

from ..helpers import BaseForm
from ..validators import validate_password_strength


class ResetChildPasswordForm(BaseForm):
    """A guardian gives their child a new password; the child's current one is not needed."""
    new_password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
        label="Bagong Password ng bata",
        help_text="Hindi bababa sa 8 character, may malaki at maliit na titik, numero, at espesyal na character (hal. ! @ # $).",
        validators=[validate_password_strength],
    )
    confirm_password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
        error_messages={"required": "Hindi magkatugma ang bagong password at kumpirmasyon."},
        label="Kumpirmahin ang Bagong Password",
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error("confirm_password", "Hindi magkatugma ang bagong password at kumpirmasyon.")
        return cleaned_data
