from django.db import models

from salitaaco.models.account_base import AccountBase


class AdminAccount(AccountBase):
    """
    The account of someone who runs the app. What an admin may open is decided
    by the Administrator group; this holds their name and picture.
    """
    ROLE_LABEL = "Admin"

    admin_account_id = models.AutoField(primary_key=True)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='admin_account')

    @property
    def role_badge_class(self):
        return "badge admin"
