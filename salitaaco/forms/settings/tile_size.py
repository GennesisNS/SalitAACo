from django import forms

from salitaaco.models.account_base import AccountBase

from ..helpers import BaseForm


class TileSizeForm(BaseForm):
    tile_size = forms.ChoiceField(
        required=True,
        choices=AccountBase.TILE_SIZE_CHOICES,
        widget=forms.RadioSelect(),
        error_messages={
            "required": "Pumili ng laki ng tile.",
            "invalid_choice": "Pumili ng laki ng tile.",
        },
        label="Laki ng tile",
    )
