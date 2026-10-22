from django import forms

from salitaaco.utils.uploads import ICON_MAX_SIDE, MAX_UPLOAD_SIZE, random_upload_name, shrink_picture

from .helpers import BaseForm
from .validators import clean_symbol, validate_image_size, validate_picture_type

EMOJI = "emoji"
IMAGE = "image"

# How to type an emoji, for the help line under an emoji field.
EMOJI_KEYS = "Sa phone, piliin ito sa emoji ng keyboard; sa Windows, pindutin ang Windows + . (tuldok); sa Mac, Control + Command + Space."


def picture_kind(thing):
    """Which picture a board or a word (models/icon_picture.py) has, as its form's choice."""
    return IMAGE if thing.has_icon_image else EMOJI


class PictureChoiceForm(BaseForm):
    """
    The form of something whose picture is an emoji or an uploaded JPG, PNG or
    WEBP picture: a guardian's board, an admin's word, a guardian's tile. A
    form says what its picture is called (`picture_label`), declares its own
    `emoji` field and says what to ask for when nothing was given. `editing`
    is the thing being changed, which keeps its uploaded picture when no new
    one is chosen.

    The choice may be left out: it is the emoji then, as before pictures could be uploaded.
    """
    picture_label = "Larawan"
    emoji_missing = "Ilagay ang emoji."
    image_missing = "Pumili ng larawan."

    icon_kind = forms.ChoiceField(
        required=False,
        choices=[(EMOJI, "Emoji"), (IMAGE, "Larawan")],
        initial=EMOJI,
        widget=forms.RadioSelect(attrs={"class": "iconKind"}),
    )
    icon_image = forms.ImageField(
        required=False,
        # Hidden: the "Pumili ng larawan" button is its label.
        widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp", "class": "hidden"}),
        error_messages={"invalid_image": "Hindi mabuksan ang larawan. Pumili ng iba."},
        validators=[validate_picture_type, validate_image_size],
        label="Larawan (JPG, PNG o WEBP)",
        help_text=f"Hanggang {MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
    )

    def __init__(self, *args, editing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editing = editing
        self.fields["icon_kind"].label = self.picture_label

    def clean_emoji(self):
        return clean_symbol(self.cleaned_data["emoji"]) if self.cleaned_data["emoji"] else ""

    def clean(self):
        cleaned_data = super().clean()
        kind = cleaned_data["icon_kind"] = cleaned_data.get("icon_kind") or EMOJI
        if kind == EMOJI and not cleaned_data.get("emoji") and "emoji" not in self.errors:
            self.add_error("emoji", self.emoji_missing)
        if kind == IMAGE and not cleaned_data.get("icon_image") and "icon_image" not in self.errors:
            keeps_its_own = self.editing is not None and self.editing.has_icon_image
            if not keeps_its_own:
                self.add_error("icon_image", self.image_missing)
        return cleaned_data

    def save_picture(self, thing):
        """
        Give `thing` the picture chosen: an uploaded one, made small enough to
        keep (utils/uploads.py), or the emoji in place of an uploaded one.
        Choosing to keep its uploaded picture leaves it as it is.
        """
        if self.cleaned_data["icon_kind"] == IMAGE:
            image = self.cleaned_data["icon_image"]
            if image:
                content, mime = shrink_picture(image, ICON_MAX_SIDE)
                thing.set_icon_image(random_upload_name(mime), content, mime)
        else:
            thing.remove_icon_image(save=False)
            thing.emoji = self.cleaned_data["emoji"]
            thing.save()
