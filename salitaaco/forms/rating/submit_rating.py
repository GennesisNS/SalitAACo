from django import forms

from ..helpers import BaseForm

MAX_COMMENT_LENGTH = 1000


class SubmitRatingForm(BaseForm):
    # The star picker on the page fills this in.
    rating = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=5,
        widget=forms.HiddenInput(),
        error_messages={
            "required": "Pumili ng 1 hanggang 5 bituin.",
            "invalid": "Pumili ng 1 hanggang 5 bituin.",
            "min_value": "Pumili ng 1 hanggang 5 bituin.",
            "max_value": "Pumili ng 1 hanggang 5 bituin.",
        },
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "textarea",
            "rows": 3,
            "placeholder": "Ano ang magagandang bahagi? Ano pa ang dapat idagdag?",
        }),
        label="Komento (opsiyonal)",
    )

    def clean_comment(self):
        # A long comment is shortened, not rejected; an empty one is stored as no comment.
        comment = self.cleaned_data.get("comment", "")
        return comment[:MAX_COMMENT_LENGTH] or None
