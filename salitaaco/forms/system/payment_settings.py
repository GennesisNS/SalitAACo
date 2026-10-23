from django import forms

from ..helpers import BaseForm
from ..validators import validate_image_size, validate_phone_number, validate_picture_type


class PaymentSettingsForm(BaseForm):
    """Where guardians send the money for a paid plan: the GCash QR code and account."""
    gcash_name = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. Juan D."}),
        label="Pangalan sa GCash (opsiyonal)",
    )
    gcash_number = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. 0917 000 0000", "inputmode": "tel"}),
        label="GCash number (opsiyonal)",
        validators=[validate_phone_number],
    )
    # Left empty, the QR code already saved stays.
    gcash_qr = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        error_messages={"invalid_image": "Hindi mabuksan ang larawan. Pumili ng iba."},
        validators=[validate_picture_type, validate_image_size],
        label="Larawan ng GCash QR code",
    )
