from django.db import migrations

# The default accounts, as MYO makes its own (its migration 0008): one of each
# kind, made on `migrate`, all with this password. An account whose username
# is already taken is left as it is.
PASSWORD = "Password@123"


def create_default_users(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")
    AdminAccount = apps.get_model("salitaaco", "AdminAccount")
    GuardianAccount = apps.get_model("salitaaco", "GuardianAccount")
    ChildAccount = apps.get_model("salitaaco", "ChildAccount")

    if not User.objects.filter(username__iexact="admin@example.com").exists():
        admin = User.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password=PASSWORD,
            first_name="Admin",
            last_name="User",
        )
        admin.groups.add(Group.objects.get_or_create(name="Administrator")[0])
        AdminAccount.objects.create(user=admin, display_name="Admin")

    guardian = GuardianAccount.objects.filter(user__username__iexact="guardian@example.com").first()
    if not User.objects.filter(username__iexact="guardian@example.com").exists():
        user = User.objects.create_user(
            username="guardian@example.com",
            email="guardian@example.com",
            password=PASSWORD,
            first_name="Guardian",
            last_name="User",
        )
        user.groups.add(Group.objects.get_or_create(name="Guardian")[0])
        guardian = GuardianAccount.objects.create(user=user, display_name="Guardian")

    if not User.objects.filter(username__iexact="child@example.com").exists():
        user = User.objects.create_user(
            username="child@example.com",
            email="child@example.com",
            password=PASSWORD,
            first_name="Child",
            last_name="User",
        )
        user.groups.add(Group.objects.get_or_create(name="Child")[0])
        ChildAccount.objects.create(user=user, display_name="Child", age=7, guardian=guardian)


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('salitaaco', '0026_generated_report'),
    ]

    operations = [
        # Going back leaves the accounts: they may be in use by then.
        migrations.RunPython(create_default_users, migrations.RunPython.noop),
    ]
