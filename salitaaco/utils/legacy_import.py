import logging

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone

from salitaaco.defaults.administrator_roles import ADMINISTRATOR
from salitaaco.defaults.user_roles import CHILD
from salitaaco.models.admin_account import AdminAccount
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.customization import Customization
from salitaaco.models.rating import Rating
from salitaaco.models.word_usage import WordUsage
from salitaaco.utils.account import add_to_group
from salitaaco.utils.uploads import base_mime, random_upload_name

logger = logging.getLogger(__name__)

# Functions that copy one row of the PHP application's database into the Django
# models. Each takes the row as a dict keyed by the old column names.


def legacy_time(value):
    """The PHP app stored local wall-clock times; make them time-zone aware."""
    if value is None:
        return None
    if timezone.is_naive(value):
        return timezone.make_aware(value)
    return value


def legacy_password(password_hash):
    """
    PHP's password_hash() output is a bcrypt hash ("$2y$..."). Django's
    BCryptPasswordHasher checks it unchanged once it carries the hasher's name.
    """
    return f"bcrypt${password_hash}"


def safe_mime(mime, family, default):
    """Keep a stored content type only if it belongs to the expected family."""
    mime = base_mime(mime)
    return mime if mime.startswith(f"{family}/") else default


def import_user(row):
    """
    Create the user and account for one row of the old `users` table: an admin
    account for an old admin, a child account (with no guardian yet) for
    everyone else. Returns the new User, or None when the username is already
    taken here.
    """
    if User.objects.filter(username__iexact=row["username"]).exists():
        logger.warning("Skipped user %s: the username already exists", row["username"])
        return None

    user = User(username=row["username"], password=legacy_password(row["password_hash"]))
    user.save()
    # date_joined defaults to now and the account's timestamps are automatic, so
    # the original times are written with update(), which bypasses both.
    User.objects.filter(pk=user.pk).update(
        date_joined=legacy_time(row["created_at"]) or timezone.now(),
        last_login=legacy_time(row.get("last_login")),
    )
    user.refresh_from_db()

    if row.get("is_admin"):
        add_to_group(user, ADMINISTRATOR)
        account = AdminAccount.objects.create(user=user, display_name=row["display_name"])
    else:
        add_to_group(user, CHILD)
        account = ChildAccount.objects.create(user=user, display_name=row["display_name"], age=row.get("age"))

    if row.get("avatar_data"):
        mime = safe_mime(row.get("avatar_mime"), "image", "application/octet-stream")
        account.set_avatar(random_upload_name(mime), ContentFile(bytes(row["avatar_data"])), mime)
    type(account).objects.filter(pk=account.pk).update(created_at=user.date_joined)

    return user


def import_customization(user, row):
    """Copy one row of the old `customizations` table, writing its blobs out as files."""
    customization = Customization.objects.create(user=user, word=row["word"])
    if row.get("image_data"):
        mime = safe_mime(row.get("image_mime"), "image", "application/octet-stream")
        customization.set_image(random_upload_name(mime), ContentFile(bytes(row["image_data"])), mime)
    if row.get("sound_data"):
        mime = safe_mime(row.get("sound_mime"), "audio", "application/octet-stream")
        customization.set_sound(random_upload_name(mime), ContentFile(bytes(row["sound_data"])), mime)
    if row.get("updated_at"):
        Customization.objects.filter(pk=customization.pk).update(updated_at=legacy_time(row["updated_at"]))
    return customization


def import_word_usage(user, row):
    """Copy one row of the old `word_usage` table."""
    usage = WordUsage.objects.create(user=user, word=row["word"], use_count=row["use_count"])
    if row.get("last_used"):
        WordUsage.objects.filter(pk=usage.pk).update(last_used=legacy_time(row["last_used"]))
    return usage


def import_rating(user, row):
    """Copy one row of the old `ratings` table."""
    rating = Rating.objects.create(user=user, rating=row["rating"], comment=row.get("comment") or None)
    Rating.objects.filter(pk=rating.pk).update(
        created_at=legacy_time(row.get("created_at")) or rating.created_at,
        updated_at=legacy_time(row.get("updated_at")) or rating.updated_at,
    )
    return rating
