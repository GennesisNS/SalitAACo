from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

BEFORE = [("salitaaco", "0018_guardian_words")]
AFTER = [("salitaaco", "0019_separate_admin_accounts")]


def migrate(target):
    """Migrate the test database to `target` and return the models as they are at that point."""
    executor = MigrationExecutor(connection)
    executor.migrate(target)
    return MigrationExecutor(connection).loader.project_state(target).apps


class SeparateAdminAccountsTest(TransactionTestCase):
    """Migration 0019 takes admin access away from accounts that are also a guardian's or a child's."""

    def setUp(self):
        # Whatever happens, leave the schema at the latest migration for the tests that run next.
        self.addCleanup(lambda: migrate(MigrationExecutor(connection).loader.graph.leaf_nodes()))

        apps = migrate(BEFORE)
        User = apps.get_model("auth", "User")
        Group = apps.get_model("auth", "Group")
        AdminAccount = apps.get_model("salitaaco", "AdminAccount")
        GuardianAccount = apps.get_model("salitaaco", "GuardianAccount")
        ChildAccount = apps.get_model("salitaaco", "ChildAccount")

        administrators, _ = Group.objects.get_or_create(name="Administrator")
        guardians, _ = Group.objects.get_or_create(name="Guardian")

        # A guardian who was given admin access, with Django's admin site too.
        nanay = User.objects.create(username="nanay", password="x", is_staff=True, is_superuser=True)
        nanay.groups.add(administrators, guardians)
        guardian = GuardianAccount.objects.create(user=nanay, display_name="Nanay Rosa")
        AdminAccount.objects.create(user=nanay, display_name="Nanay Rosa")
        ChildAccount.objects.create(user=User.objects.create(username="miguel", password="x"),
                                    display_name="Miguel", guardian=guardian)

        # A child who was given admin access.
        ana = User.objects.create(username="ana", password="x")
        ana.groups.add(administrators)
        ChildAccount.objects.create(user=ana, display_name="Ana")
        AdminAccount.objects.create(user=ana, display_name="Ana")

        # An admin who is only an admin.
        developer = User.objects.create(username="developer", password="x", is_staff=True, is_superuser=True)
        developer.groups.add(administrators)
        AdminAccount.objects.create(user=developer, display_name="Developer")

    def test_only_admin_only_accounts_stay_admins(self):
        apps = migrate(AFTER)
        User = apps.get_model("auth", "User")
        AdminAccount = apps.get_model("salitaaco", "AdminAccount")
        GuardianAccount = apps.get_model("salitaaco", "GuardianAccount")

        self.assertEqual(list(AdminAccount.objects.values_list("user__username", flat=True)), ["developer"])
        self.assertEqual(
            list(User.objects.filter(groups__name="Administrator").values_list("username", flat=True)), ["developer"],
        )

        nanay = User.objects.get(username="nanay")
        self.assertEqual(list(nanay.groups.values_list("name", flat=True)), ["Guardian"])
        self.assertFalse(nanay.is_staff or nanay.is_superuser)
        # She is the guardian she was, with her child.
        self.assertEqual(GuardianAccount.objects.get(user=nanay).children.count(), 1)

        developer = User.objects.get(username="developer")
        self.assertTrue(developer.is_staff and developer.is_superuser)
        self.assertTrue(User.objects.get(username="ana").child_account)
