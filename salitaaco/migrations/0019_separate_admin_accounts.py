from django.core.files.storage import default_storage
from django.db import migrations
from django.db.models import Q

ADMINISTRATOR = "Administrator"


def separate_admin_accounts(apps, schema_editor):
    """
    An admin is an account of its own from now on, never a guardian's or a
    child's. An account that is both loses its admin access, and is again
    only the guardian or child it was; new admins are made as new accounts.
    """
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")
    AdminAccount = apps.get_model("salitaaco", "AdminAccount")

    administrators = Group.objects.filter(name=ADMINISTRATOR).first()
    if administrators is None:
        return

    both = User.objects.filter(groups=administrators).filter(
        Q(guardian_account__isnull=False) | Q(child_account__isnull=False)
    ).distinct()
    for user in both:
        user.groups.remove(administrators)
        user.is_staff = False
        user.is_superuser = False
        user.save(update_fields=["is_staff", "is_superuser"])
        for admin_account in AdminAccount.objects.filter(user=user):
            if admin_account.avatar:
                default_storage.delete(admin_account.avatar.name)
            admin_account.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('salitaaco', '0018_guardian_words'),
    ]

    operations = [
        # Which accounts were admins is not kept, so this cannot be undone; going back leaves them as they are.
        migrations.RunPython(separate_admin_accounts, migrations.RunPython.noop),
    ]
