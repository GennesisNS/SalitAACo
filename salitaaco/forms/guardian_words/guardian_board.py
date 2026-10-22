from django import forms

from salitaaco.utils.board import every_board_name

from ..picture_choice import EMOJI_KEYS, PictureChoiceForm


class GuardianBoardForm(PictureChoiceForm):
    """
    A board a guardian makes for their family, or changes: a name no other
    board of theirs or the app's has, and its picture, an emoji or an uploaded
    one. `editing` is the GuardianBoard being changed, so that it is not taken
    for a copy of itself and keeps its picture when no new one is chosen.
    """
    picture_label = "Larawan ng board"
    emoji_missing = "Ilagay ang emoji ng board."
    image_missing = "Pumili ng larawan ng board."

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
    emoji = forms.CharField(
        required=False,
        max_length=16,
        widget=forms.TextInput(attrs={"class": "input emojiInput"}),
        error_messages={"max_length": "Isang emoji lang ang larawan."},
        label="Emoji",
        help_text=f"Isang emoji lang, hal. 🏫 para sa paaralan. {EMOJI_KEYS}",
    )

    def __init__(self, *args, guardian, editing=None, **kwargs):
        super().__init__(*args, editing=editing, **kwargs)
        self.guardian = guardian

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        # Tiles and a child's switches find a board by its name, so no two may share one.
        others = self.guardian.boards.exclude(pk=self.editing.pk) if self.editing else self.guardian.boards.all()
        taken = every_board_name() + list(others.values_list("name", flat=True))
        if name.lower() in (other.lower() for other in taken):
            raise forms.ValidationError("May board na may ganitong pangalan.")
        return name
