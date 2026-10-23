from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from salitaaco.utils.uploads import IMAGE_MIME_TYPES, MAX_UPLOAD_SIZE, PICTURE_MIME_TYPES, base_mime

import re


MIN_USERNAME_LENGTH = 3
MAX_PASSWORD_LENGTH = 128


def username_exists(value):
    if User.objects.filter(username__iexact=value).exists():
        raise ValidationError("Ginagamit na ang username na ito.")


def validate_username(value):
    """
    A username to log in with, typed on a phone or by a child: letters,
    numbers, and the dot, dash and underscore, without spaces.
    """
    if len(value) < MIN_USERNAME_LENGTH:
        raise ValidationError(f"Hindi bababa sa {MIN_USERNAME_LENGTH} character ang username.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise ValidationError("Mga titik, numero, tuldok (.), gitling (-) at underscore (_) lang ang puwede sa username, walang espasyo.")


def validate_phone_number(value):
    """A telephone or GCash number as people write it: digits, with spaces, dashes, brackets or a leading +."""
    if not re.fullmatch(r"\+?[0-9 ()-]+", value):
        raise ValidationError("Mga numero lang ang puwede, hal. 0917 000 0000.")
    digits = len(re.sub(r"\D", "", value))
    if not 7 <= digits <= 15:
        raise ValidationError("Hindi tama ang haba ng numero (7 hanggang 15 digit).")


def check_tile_word(word, words):
    """
    A word that one of the user's tiles says. `words` is every word their
    boards have (utils/board.board_words); None checks nothing.
    """
    if words is not None and word not in words:
        raise ValidationError("Walang ganitong tile sa board.")
    return word


def validate_image_type(file):
    if base_mime(getattr(file, "content_type", "")) not in IMAGE_MIME_TYPES:
        raise ValidationError("Hindi suportadong file type ng larawan.")


def validate_picture_type(file):
    if base_mime(getattr(file, "content_type", "")) not in PICTURE_MIME_TYPES:
        raise ValidationError("JPEG, PNG o WebP lang ang puwedeng larawan.")


def validate_image_size(file):
    if file.size > MAX_UPLOAD_SIZE:
        raise ValidationError("Masyadong malaki ang larawan (max 5MB).")


def validate_sound_type(file):
    if not base_mime(getattr(file, "content_type", "")).startswith("audio/"):
        raise ValidationError("Hindi suportadong file type ng tunog.")


def validate_sound_size(file):
    if file.size > MAX_UPLOAD_SIZE:
        raise ValidationError("Masyadong malaki ang tunog (max 5MB).")


def validate_voice_sample_size(file):
    # A minute or two of speech; an uncompressed WAV of that length is about 10 MB.
    if file.size > 2 * MAX_UPLOAD_SIZE:
        raise ValidationError("Masyadong malaki ang recording (max 10MB).")


# A keycap emoji (0️⃣ to 9️⃣, #️⃣, *️⃣) is a digit, "#" or "*", an optional
# variation selector (U+FE0F) and the combining enclosing keycap (U+20E3).
KEYCAP_EMOJI = re.compile("[0-9#*]️?⃣")


def clean_symbol(value):
    """
    A tile's or a board's picture: an emoji. Letters and digits would be a
    second label, not a picture; a digit inside a keycap emoji is the emoji's
    own, so keycaps are taken out before looking for them.
    """
    symbol = value.strip()
    if re.search(r"[A-Za-z0-9<>&]", KEYCAP_EMOJI.sub("", symbol)):
        raise ValidationError("Emoji ang ilagay, hindi titik o numero.")
    return symbol


def name_validator(value):
    """
    A person's name as Filipinos write it: letters of any alphabet (ñ, é),
    spaces, and the dash, apostrophe and dot of "Ma. Teresa", "Dela Cruz-Reyes"
    or "D'Souza". It starts with a letter.
    """
    if not re.fullmatch(r"[^\W\d_](?:[^\W\d_]|[ .'’-])*", value):
        raise ValidationError("Mga titik, espasyo, gitling (-), kudlit (') at tuldok (.) lang ang puwede sa pangalan.")


def validate_password_strength(value):
    if len(value) < 8:
        raise ValidationError("Hindi bababa sa 8 character ang password.")
    if len(value) > MAX_PASSWORD_LENGTH:
        raise ValidationError(f"Hanggang {MAX_PASSWORD_LENGTH} character lang ang password.")
    if not re.search(r'[A-Z]', value):
        raise ValidationError("Kailangang may kahit isang malaking titik ang password.")
    if not re.search(r'[a-z]', value):
        raise ValidationError("Kailangang may kahit isang maliit na titik ang password.")
    if not re.search(r'\d', value):
        raise ValidationError("Kailangang may kahit isang numero ang password.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError("Kailangang may kahit isang espesyal na character ang password (hal. ! @ # $).")