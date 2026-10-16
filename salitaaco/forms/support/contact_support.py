from django import forms

from ..helpers import BaseForm

NO_CHILD = ""


class ContactSupportForm(BaseForm):
    """A guardian's message to the people who run the app, optionally about one of their children."""
    child = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"class": "select"}),
        error_messages={"invalid_choice": "Pumili ng bata mula sa listahan."},
        label="Batang apektado (opsiyonal)",
    )
    message = forms.CharField(
        required=True,
        max_length=2000,
        widget=forms.Textarea(attrs={
            "class": "textarea",
            "rows": 4,
            "placeholder": "Ano ang nangyari? Saang pahina o board?",
        }),
        error_messages={
            "required": "Ilarawan ang problema o tanong.",
            "max_length": "Masyadong mahaba ang mensahe (hanggang 2000 character).",
        },
        label="Ilarawan ang problema o tanong",
        help_text="Huwag isama ang mga pangungusap na binuo ng bata o anumang pribadong detalye na hindi kailangan.",
    )

    def __init__(self, *args, children=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.children = {str(child.uuid): child for child in children}
        self.fields["child"].choices = [(NO_CHILD, "Wala")] + [
            (uuid, child.display_name) for uuid, child in self.children.items()
        ]

    def chosen_child(self):
        return self.children.get(self.cleaned_data.get("child"))
