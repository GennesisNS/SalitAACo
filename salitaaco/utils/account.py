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
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.payment import Payment
from salitaaco.utils.family_voice import delete_family_voice
from salitaaco.utils.guardian_words import delete_shared_audio_if_unused

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


def grant_admin(user):
    """
    Give an account access to the admin pages. An admin account is added next
    to whatever account the user already has, which keeps a guardian's
    children and a child's guardian in place.
    """
    if not AdminAccount.objects.filter(user=user).exists():
        existing_account = find_user_account(user)
        AdminAccount.objects.create(
            user=user,
            display_name=existing_account.display_name if existing_account else user.username,
        )
    add_to_group(user, ADMINISTRATOR)


def revoke_admin(user):
    """
    Take admin access away, with access to Django's admin site. The admin
    account goes too; a guardian or child account the user also has is left as
    it is, and is what they are from now on.
    """
    user.groups.remove(*Group.objects.filter(name=ADMINISTRATOR))
    user.is_staff = False
    user.is_superuser = False
    user.save()
    for admin_account in AdminAccount.objects.filter(user=user):
        admin_account.remove_avatar(save=False)
        admin_account.delete()


def home_route(account):
    """The URL name of the page an account lands on after logging in: a child's board, a guardian's overview, an admin's dashboard."""
    if isinstance(account, AdminAccount):
        return "analytics"
    if isinstance(account, GuardianAccount):
        return "overview"
    return "board"


def request_account(request):
    """The logged-in user's account, looked up once per request however many times it is asked for."""
    if not hasattr(request, "_account"):
        request._account = get_user_account(request.user)
    return request._account


def delete_user_account(user):
    """
    Permanently delete an account with everything it owns: its admin, guardian
    or child account, custom pictures and recordings, usage counts and rating,
    and a guardian's family voices (at ElevenLabs too) and payments. The rows
    go through the database cascade; the uploaded files are removed from
    storage afterwards.
    """
    # The account is going regardless, so an ElevenLabs refusal is logged, not raised.
    for voice in FamilyVoice.objects.filter(guardian__user=user):
        delete_family_voice(voice, strict=False)

    file_names = []
    for customization in Customization.objects.filter(user=user):
        file_names += [customization.image.name, customization.sound.name]
    for payment in Payment.objects.filter(guardian__user=user):
        file_names.append(payment.proof.name)
    # A guardian's own tiles go with the account; their audio in the shared voice once no one else's tile says the word.
    own_words = list(GuardianWord.objects.filter(guardian__user=user).values_list("word", flat=True))
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
    for word in own_words:
        delete_shared_audio_if_unused(word)

    logger.info("Deleted account %s", username)
