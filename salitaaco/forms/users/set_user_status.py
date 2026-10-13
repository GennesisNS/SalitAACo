from django import forms

from ..helpers import BaseForm


class SetUserStatusForm(BaseForm):
    """
    Makes an account active or inactive. An inactive account cannot log in and
    is logged out where it is logged in; nothing of it is deleted.
    """
    active = forms.BooleanField(required=False)

    def __init__(self, *args, acting_user=None, target_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.acting_user = acting_user
        self.target_user = target_user

    def clean(self):
        cleaned_data = super().clean()
        # An admin who made their own account inactive could not come back to undo it.
        if not cleaned_data.get("active") and self.target_user == self.acting_user:
            raise forms.ValidationError("Hindi mo magagawang hindi aktibo ang sarili mong account.")
        return cleaned_data
