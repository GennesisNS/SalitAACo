from django import forms

from ..helpers import BaseForm

MAX_LIMIT = 500


def limit_field(label):
    return forms.IntegerField(
        required=True,
        min_value=0,
        max_value=MAX_LIMIT,
        widget=forms.NumberInput(attrs={"class": "input", "min": 0, "max": MAX_LIMIT}),
        error_messages={
            "required": "Ilagay ang bilang.",
            "invalid": "Hindi tama ang bilang.",
            "min_value": "Hindi tama ang bilang.",
            "max_value": f"Hanggang {MAX_LIMIT} lang.",
        },
        label=label,
    )


class PlanLimitsForm(BaseForm):
    """
    How many tiles and boards of their own a guardian can add on the free plan
    and on a paid plan (SalitAACo Plus), each across all of the guardian's
    family's boards. The page shows them grouped by plan, so each label only
    says what is counted.
    """
    free_word_limit = limit_field("Sariling tile")
    free_board_limit = limit_field("Custom board")
    plus_word_limit = limit_field("Sariling tile")
    plus_board_limit = limit_field("Custom board")
