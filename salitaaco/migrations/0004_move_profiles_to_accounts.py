from django.db import migrations

ADMINISTRATOR = "Administrator"
CHILD = "Child"
GUARDIAN = "Guardian"

def copy_fields(source):
    return {
        "uuid": source.uuid,
        "display_name": source.display_name,
        # The picture file stays where it is; only its name is carried over.
        "avatar": source.avatar.name,
        "avatar_mime": source.avatar_mime,
    }


def keep_timestamps(model, account, source):
    # created_at and updated_at fill themselves in on save, so the original
    # times are written with update(), which leaves them alone.
    model.objects.filter(pk=account.pk).update(created_at=source.created_at, updated_at=source.updated_at)


def profiles_to_accounts(apps, schema_editor):
    """
    Every existing profile becomes one of the new accounts: an admin account
    for members of the Administrator group, a child account (with no guardian
    yet) for everyone else. Guardians did not exist before this migration.
    """
    Group = apps.get_model("auth", "Group")
    Profile = apps.get_model("salitaaco", "Profile")
    AdminAccount = apps.get_model("salitaaco", "AdminAccount")
    ChildAccount = apps.get_model("salitaaco", "ChildAccount")

    child_group, _ = Group.objects.get_or_create(name=CHILD)
    Group.objects.get_or_create(name=GUARDIAN)

    for profile in Profile.objects.select_related("user"):
        if profile.user.groups.filter(name=ADMINISTRATOR).exists():
            account = AdminAccount.objects.create(user=profile.user, **copy_fields(profile))
            keep_timestamps(AdminAccount, account, profile)
        else:
            account = ChildAccount.objects.create(user=profile.user, age=profile.age, **copy_fields(profile))
            keep_timestamps(ChildAccount, account, profile)
            profile.user.groups.add(child_group)


def accounts_to_profiles(apps, schema_editor):
    """Put the accounts back into profiles. A user with more than one account keeps the first found."""
    Group = apps.get_model("auth", "Group")
    Profile = apps.get_model("salitaaco", "Profile")

    for model_name in ["AdminAccount", "GuardianAccount", "ChildAccount"]:
        Account = apps.get_model("salitaaco", model_name)
        for account in Account.objects.select_related("user"):
            if Profile.objects.filter(user=account.user).exists():
                continue
            profile = Profile.objects.create(
                user=account.user,
                age=getattr(account, "age", None),
                **copy_fields(account),
            )
            keep_timestamps(Profile, profile, account)

    Group.objects.filter(name__in=[CHILD, GUARDIAN]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('salitaaco', '0003_child_guardian_admin_accounts'),
    ]

    operations = [
        migrations.RunPython(profiles_to_accounts, accounts_to_profiles),
    ]
