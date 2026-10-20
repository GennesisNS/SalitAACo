from django import forms

from salitaaco.utils.board import every_board_name

from ..helpers import BaseForm
from ..validators import clean_symbol


class GuardianBoardForm(BaseForm):
    """A board a guardian makes for their family: a name no other board of theirs or the app's has, and its picture."""
    name = forms.CharField(
        required=True,
        max_length=40,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. Bahay ni Lola"}),
        error_messages={
            "required": "Ilagay ang pangalan ng board.",
            "max_length": "Masyadong mahaba ang pangalan (hanggang 40 character).",
        },
        label="Pangalan ng board",
    )
    emoji = forms.CharField(
        required=True,
        max_length=16,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. 🏡"}),
        error_messages={
            "required": "Ilagay ang larawan ng board.",
            "max_length": "Isang emoji lang ang larawan.",
        },
        label="Larawan (emoji)",
    )

    def __init__(self, *args, guardian, **kwargs):
        super().__init__(*args, **kwargs)
        self.guardian = guardian

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        # Tiles and a child's switches find a board by its name, so no two may share one.
        taken = every_board_name() + list(self.guardian.boards.values_list("name", flat=True))
        if name.lower() in (other.lower() for other in taken):
            raise forms.ValidationError("May board na may ganitong pangalan.")
        return name

    def clean_emoji(self):
        return clean_symbol(self.cleaned_data["emoji"])
