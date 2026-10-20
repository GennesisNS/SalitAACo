from django import forms

from ..helpers import BaseForm


class RemoveAdminForm(BaseForm):
    """Deletes an admin's account. An admin cannot delete their own here."""

    def __init__(self, *args, acting_user=None, target_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.acting_user = acting_user
        self.target_user = target_user

    def clean(self):
        cleaned_data = super().clean()
        # Whoever is removing is an admin, so removing only others always leaves one.
        if self.target_user == self.acting_user:
            raise forms.ValidationError("Hindi mo mabubura ang sarili mong admin account dito.")
        return cleaned_data
