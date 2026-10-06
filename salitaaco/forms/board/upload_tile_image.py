from django import forms

from ..helpers import BaseForm
from ..validators import validate_image_size, validate_image_type


class UploadTileImageForm(BaseForm):
    word = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.HiddenInput(attrs={"id": "tileImageWord"}),
        error_messages={"required": "Walang natanggap na larawan."},
    )
    image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={"id": "tileImageFile", "accept": "image/*", "class": "hidden"}),
        error_messages={
            "required": "Walang natanggap na larawan.",
            "empty": "Walang natanggap na larawan.",
            "invalid_image": "Hindi suportadong file type ng larawan.",
        },
        validators=[validate_image_type, validate_image_size],
    )
