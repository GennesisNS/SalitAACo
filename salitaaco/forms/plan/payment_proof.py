from django import forms

from ..helpers import BaseForm
from ..validators import validate_image_size, validate_picture_type


class PaymentProofForm(BaseForm):
    """The picture of a GCash payment a guardian sends for a paid plan."""
    plan = forms.ChoiceField(
        required=True,
        widget=forms.HiddenInput(),
        error_messages={
            "required": "Hindi na iniaalok ang planong ito.",
            "invalid_choice": "Hindi na iniaalok ang planong ito.",
        },
    )
    proof = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={"id": "proofFile", "accept": "image/jpeg,image/png,image/webp"}),
        error_messages={
            "required": "Pumili ng larawan ng matagumpay na bayad.",
            "empty": "Pumili ng larawan ng matagumpay na bayad.",
            "invalid_image": "Hindi mabuksan ang larawan. Pumili ng iba.",
        },
        validators=[validate_picture_type, validate_image_size],
        label="Larawan ng matagumpay na bayad",
    )

    def __init__(self, *args, plans=(), **kwargs):
        """plans: the paid plans that can be paid for."""
        super().__init__(*args, **kwargs)
        self.fields["plan"].choices = [(plan.key, plan.name) for plan in plans]
