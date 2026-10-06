from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from salitaaco.utils.uploads import IMAGE_MIME_TYPES, MAX_UPLOAD_SIZE, base_mime


def username_exists(value):
    if User.objects.filter(username__iexact=value).exists():
        raise ValidationError("Ginagamit na ang username na ito.")


def validate_image_type(file):
    if base_mime(getattr(file, "content_type", "")) not in IMAGE_MIME_TYPES:
        raise ValidationError("Hindi suportadong file type ng larawan.")


def validate_image_size(file):
    if file.size > MAX_UPLOAD_SIZE:
        raise ValidationError("Masyadong malaki ang larawan (max 5MB).")


def validate_sound_type(file):
    if not base_mime(getattr(file, "content_type", "")).startswith("audio/"):
        raise ValidationError("Hindi suportadong file type ng tunog.")


def validate_sound_size(file):
    if file.size > MAX_UPLOAD_SIZE:
        raise ValidationError("Masyadong malaki ang tunog (max 5MB).")
