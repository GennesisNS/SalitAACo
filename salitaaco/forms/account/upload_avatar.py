from django import forms

from ..helpers import BaseForm
from ..validators import validate_image_size, validate_image_type


class UploadAvatarForm(BaseForm):
    avatar = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={"id": "avatarFile", "accept": "image/*", "class": "hidden"}),
        error_messages={
            "required": "Walang natanggap na larawan.",
            "empty": "Walang natanggap na larawan.",
            "invalid_image": "Hindi suportadong file type ng larawan.",
        },
        validators=[validate_image_type, validate_image_size],
    )
