import logging

from django.contrib.auth.models import Group
from django.core.files.storage import default_storage
from django.db import transaction

from salitaaco.defaults.administrator_roles import ADMINISTRATOR
from salitaaco.defaults.user_roles import GUARDIAN
from salitaaco.models.admin_account import AdminAccount
from salitaaco.models.customization import Customization
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.utils.family_voice import delete_family_voice

logger = logging.getLogger(__name__)

# The names under which a User reaches each kind of account, in the order they
# are looked for. Someone with more than one is shown as the first.
ACCOUNT_RELATIONS = ["admin_account", "guardian_account", "child_account"]


def add_to_group(user, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)


def find_user_account(user):
    """The user's admin, guardian or child account, or None when they have none."""
    for relation in ACCOUNT_RELATIONS:
        account = getattr(user, relation, None)
        if account is not None:
            return account
    return None


def get_user_account(user):
    """
    The user's account. Users made outside the app (createsuperuser, the Django
    admin) have none yet, so one is created with the username as the name: an
    admin account for staff and members of the Administrator group, a guardian
    account for anyone else.
    """
    account = find_user_account(user)
    if account is not None:
        return account

    if user.is_staff or user.is_superuser or user.groups.filter(name=ADMINISTRATOR).exists():
        add_to_group(user, ADMINISTRATOR)
        return AdminAccount.objects.create(user=user, display_name=user.username)

    add_to_group(user, GUARDIAN)
    return GuardianAccount.objects.create(user=user, display_name=user.username)


def delete_user_account(user):
    """
    Permanently delete an account with everything it owns: its admin, guardian
    or child account, custom pictures and recordings, usage counts and rating,
    and a guardian's family voices (at ElevenLabs too). The rows go through the
    database cascade; the uploaded files are removed from storage afterwards.
    """
    # The account is going regardless, so an ElevenLabs refusal is logged, not raised.
    for voice in FamilyVoice.objects.filter(guardian__user=user):
        delete_family_voice(voice, strict=False)

    file_names = []
    for customization in Customization.objects.filter(user=user):
        file_names += [customization.image.name, customization.sound.name]
    for relation in ACCOUNT_RELATIONS:
        account = getattr(user, relation, None)
        if account is not None:
            file_names.append(account.avatar.name)

    username = user.username
    with transaction.atomic():
        user.delete()

    for file_name in filter(None, file_names):
        try:
            default_storage.delete(file_name)
        except OSError:
            logger.exception("Could not delete upload %s of deleted account %s", file_name, username)

    logger.info("Deleted account %s", username)
