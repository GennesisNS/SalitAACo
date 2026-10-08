from django.db import models

from salitaaco.models.account_base import AccountBase


class GuardianAccount(AccountBase):
    """
    The account of a parent or carer. Guardians are the ones who sign up; they
    then create and manage the accounts of their children (`children`), and can
    use the board themselves.
    """
    ROLE_LABEL = "Tagapag-alaga"

    guardian_account_id = models.AutoField(primary_key=True)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='guardian_account')
