import logging

from django.core.files.storage import default_storage
from django.db import transaction

from salitaaco.models.customization import Customization
from salitaaco.models.profile import Profile

logger = logging.getLogger(__name__)


def delete_user_account(user):
    """
    Permanently delete an account with everything it owns: profile, custom
    pictures and recordings, usage counts and rating. The rows go through the
    database cascade; the uploaded files are removed from storage afterwards.
    """
    file_names = []
    for customization in Customization.objects.filter(user=user):
        file_names += [customization.image.name, customization.sound.name]
    for profile in Profile.objects.filter(user=user):
        file_names.append(profile.avatar.name)

    username = user.username
    with transaction.atomic():
        user.delete()

    for file_name in filter(None, file_names):
        try:
            default_storage.delete(file_name)
        except OSError:
            logger.exception("Could not delete upload %s of deleted account %s", file_name, username)

    logger.info("Deleted account %s", username)
