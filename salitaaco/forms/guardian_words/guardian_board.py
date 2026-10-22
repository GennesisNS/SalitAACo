from django import forms

from salitaaco.utils.board import every_board_name
from salitaaco.utils.uploads import MAX_UPLOAD_SIZE

from ..helpers import BaseForm
from ..validators import clean_symbol, validate_image_size, validate_picture_type

EMOJI = "emoji"
IMAGE = "image"


class GuardianBoardForm(BaseForm):
    """
    A board a guardian makes for their family, or changes: a name no other
    board of theirs or the app's has, and its picture, an emoji or an uploaded
    one. `editing` is the GuardianBoard being changed, so that it is not taken
    for a copy of itself and keeps its picture when no new one is chosen.
    """
    name = forms.CharField(
        required=True,
        max_length=40,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. Paaralan"}),
        error_messages={
            "required": "Ilagay ang pangalan ng board.",
            "max_length": "Masyadong mahaba ang pangalan (hanggang 40 character).",
        },
        label="Pangalan ng board",
    )
    icon_kind = forms.ChoiceField(
        required=True,
        choices=[(EMOJI, "Emoji"), (IMAGE, "Larawan")],
        initial=EMOJI,
        widget=forms.RadioSelect(attrs={"class": "iconKind"}),
        label="Larawan ng board",
    )
    emoji = forms.CharField(
        required=False,
        max_length=16,
        widget=forms.TextInput(attrs={"class": "input emojiInput"}),
        error_messages={"max_length": "Isang emoji lang ang larawan."},
        label="Emoji",
        help_text=(
            "Isang emoji lang, hal. 🏫 para sa paaralan. Sa phone, piliin ito sa emoji ng keyboard; "
            "sa Windows, pindutin ang Windows + . (tuldok); sa Mac, Control + Command + Space."
        ),
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

    def __init__(self, *args, guardian, editing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.guardian = guardian
        self.editing = editing

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        # Tiles and a child's switches find a board by its name, so no two may share one.
        others = self.guardian.boards.exclude(pk=self.editing.pk) if self.editing else self.guardian.boards.all()
        taken = every_board_name() + list(others.values_list("name", flat=True))
        if name.lower() in (other.lower() for other in taken):
            raise forms.ValidationError("May board na may ganitong pangalan.")
        return name

    def clean_emoji(self):
        return clean_symbol(self.cleaned_data["emoji"]) if self.cleaned_data["emoji"] else ""

    def clean(self):
        cleaned_data = super().clean()
        kind = cleaned_data.get("icon_kind")
        if kind == EMOJI and not cleaned_data.get("emoji") and "emoji" not in self.errors:
            self.add_error("emoji", "Ilagay ang emoji ng board.")
        if kind == IMAGE and not cleaned_data.get("icon_image") and "icon_image" not in self.errors:
            keeps_its_own = self.editing is not None and self.editing.has_icon_image
            if not keeps_its_own:
                self.add_error("icon_image", "Pumili ng larawan ng board.")
        return cleaned_data
