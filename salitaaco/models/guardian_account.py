from django.db import models

from salitaaco.models.account_base import AccountBase


class GuardianAccount(AccountBase):
    """
    The account of a parent or carer. Guardians are the ones who sign up; they
    then create and manage the accounts of their children (`children`), and can
    use the board themselves. Their email is the User's own.
    """
    ROLE_LABEL = "Tagapag-alaga"

    guardian_account_id = models.AutoField(primary_key=True)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='guardian_account')
    # Asked on sign-up; empty for guardians who signed up before it was.
    age = models.PositiveSmallIntegerField(blank=True, null=True)
    # When the guardian agreed to the privacy notice on sign-up, and which version of it.
    # Empty for guardians who signed up before there was one.
    privacy_consent_at = models.DateTimeField(blank=True, null=True)
    privacy_consent_version = models.CharField(max_length=20, blank=True)
