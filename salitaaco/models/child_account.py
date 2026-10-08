from django.db import models

from salitaaco.models.account_base import AccountBase


class ChildAccount(AccountBase):
    """
    The account of a child who talks with the board. A child logs in with their
    own username and password. Their guardian, when they have one, can manage
    the account for them; accounts that existed before guardians did have none.
    """
    ROLE_LABEL = "Bata"

    child_account_id = models.AutoField(primary_key=True)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='child_account')
    guardian = models.ForeignKey(
        'GuardianAccount',
        on_delete=models.PROTECT,
        related_name='children',
        blank=True,
        null=True,
    )
    age = models.PositiveIntegerField(blank=True, null=True)
