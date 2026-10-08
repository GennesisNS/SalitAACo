from datetime import datetime, timezone

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

BEFORE = [("salitaaco", "0002_seed_roles")]
AFTER = [("salitaaco", "0005_delete_profile")]

CREATED = datetime(2026, 9, 1, 8, 30, tzinfo=timezone.utc)


def migrate(target):
    """Migrate the test database to `target` and return the models as they are at that point."""
    executor = MigrationExecutor(connection)
    executor.migrate(target)
    return MigrationExecutor(connection).loader.project_state(target).apps


class MoveProfilesToAccountsTest(TransactionTestCase):
    """Migrations 0003 to 0005 replace Profile with the child, guardian and admin accounts."""

    def setUp(self):
        # Whatever happens, leave the schema at the latest migration for the tests that run next.
        self.addCleanup(lambda: migrate(MigrationExecutor(connection).loader.graph.leaf_nodes()))

        apps = migrate(BEFORE)
        User = apps.get_model("auth", "User")
        Group = apps.get_model("auth", "Group")
        Profile = apps.get_model("salitaaco", "Profile")

        miguel = User.objects.create(username="miguel", password="x")
        profile = Profile.objects.create(
            user=miguel, display_name="Miguel", age=7, avatar="avatars/miguel.png", avatar_mime="image/png",
        )
        Profile.objects.filter(pk=profile.pk).update(created_at=CREATED, updated_at=CREATED)
        self.miguel_uuid = profile.uuid

        # Migration 0002 seeds this group, but the test database is emptied between these tests.
        administrators, _ = Group.objects.get_or_create(name="Administrator")
        developer = User.objects.create(username="developer", password="x")
        developer.groups.add(administrators)
        Profile.objects.create(user=developer, display_name="Developer", age=30)

        # A user who never had a profile gets no account either.
        User.objects.create(username="walangprofile", password="x")

    def test_profiles_become_child_and_admin_accounts(self):
        apps = migrate(AFTER)
        Group = apps.get_model("auth", "Group")
        ChildAccount = apps.get_model("salitaaco", "ChildAccount")
        GuardianAccount = apps.get_model("salitaaco", "GuardianAccount")
        AdminAccount = apps.get_model("salitaaco", "AdminAccount")

        child = ChildAccount.objects.get()
        self.assertEqual(child.user.username, "miguel")
        self.assertEqual((child.display_name, child.age, child.guardian), ("Miguel", 7, None))
        self.assertEqual((child.avatar.name, child.avatar_mime), ("avatars/miguel.png", "image/png"))
        self.assertEqual((child.uuid, child.created_at, child.updated_at), (self.miguel_uuid, CREATED, CREATED))
        self.assertEqual(list(child.user.groups.values_list("name", flat=True)), ["Child"])

        admin = AdminAccount.objects.get()
        self.assertEqual((admin.user.username, admin.display_name), ("developer", "Developer"))
        self.assertEqual(list(admin.user.groups.values_list("name", flat=True)), ["Administrator"])

        self.assertFalse(GuardianAccount.objects.exists())
        self.assertEqual(
            sorted(Group.objects.values_list("name", flat=True)), ["Administrator", "Child", "Guardian"],
        )
        with self.assertRaises(LookupError):
            apps.get_model("salitaaco", "Profile")
        self.assertNotIn("salitaaco_profile", connection.introspection.table_names())

    def test_going_back_restores_the_profiles(self):
        migrate(AFTER)
        apps = migrate(BEFORE)
        Profile = apps.get_model("salitaaco", "Profile")
        Group = apps.get_model("auth", "Group")

        profiles = {profile.user.username: profile for profile in Profile.objects.select_related("user")}
        self.assertEqual(sorted(profiles), ["developer", "miguel"])
        miguel = profiles["miguel"]
        self.assertEqual((miguel.display_name, miguel.age, miguel.avatar.name), ("Miguel", 7, "avatars/miguel.png"))
        self.assertEqual((miguel.uuid, miguel.created_at), (self.miguel_uuid, CREATED))
        # An admin's age was not carried into the admin account, so it does not come back.
        self.assertIsNone(profiles["developer"].age)
        self.assertEqual(list(Group.objects.values_list("name", flat=True)), ["Administrator"])
        self.assertNotIn("salitaaco_childaccount", connection.introspection.table_names())
