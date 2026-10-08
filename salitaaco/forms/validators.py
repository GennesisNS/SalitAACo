from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from salitaaco.utils.uploads import IMAGE_MIME_TYPES, MAX_UPLOAD_SIZE, base_mime

import re


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


def name_validator(value):
    # only allow a-z, A-Z, dash, and space
    if not re.match(r'^[a-zA-Z\s-]+$', value):
        raise ValidationError("Name can only contain letters, spaces, and dashes.")
    
    
def validate_password_strength(value):
    if len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', value):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', value):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r'\d', value):
        raise ValidationError("Password must contain at least one number.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError("Password must contain at least one special character.")


def validate_passwords_match(password, retype_password):
    if password != retype_password:
        raise ValidationError("Passwords do not match.")