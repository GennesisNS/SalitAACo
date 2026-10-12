from django import forms

from ..helpers import BaseForm
from ..validators import validate_sound_type, validate_voice_sample_size


class AddFamilyVoiceForm(BaseForm):
    name = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. Nanay, Tatay, Lola Rosa"}),
        error_messages={"required": "Ilagay kung kaninong boses ito."},
        label="Kaninong boses ito?",
    )
    sample = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={"id": "voiceSampleFile", "accept": "audio/*"}),
        error_messages={
            "required": "Mag-record o mag-upload muna ng boses.",
            "empty": "Mag-record o mag-upload muna ng boses.",
        },
        label="Recording ng boses",
        validators=[validate_sound_type, validate_voice_sample_size],
    )
    consent = forms.BooleanField(
        required=True,
        error_messages={"required": "Kailangang sumang-ayon sa Paalala at Kasunduan bago gawin ang boses."},
        label="Nabasa ko at sumasang-ayon ako sa Paalala at Kasunduan.",
    )
