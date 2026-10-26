from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from salitaaco.models.admin_account import AdminAccount
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.utils.perms_check import user_roles

PASSWORD = "Password@123"


class DefaultUsersMigrationTest(TestCase):
    """Migration 0027 makes one account of each kind, as MYO's migrations make its default users."""

    def test_one_account_of_each_kind_is_made_on_migrate(self):
        admin = AdminAccount.objects.get(user__username="admin@example.com")
        guardian = GuardianAccount.objects.get(user__username="guardian@example.com")
        child = ChildAccount.objects.get(user__username="child@example.com")
        self.assertEqual(child.guardian, guardian)
        self.assertEqual(
            [user_roles(account.user) for account in [admin, guardian, child]],
            [{"Administrator"}, {"Guardian"}, {"Child"}],
        )
        # As MYO's default admin, a superuser, with its email.
        self.assertTrue(admin.user.is_superuser and admin.user.is_staff)
        self.assertEqual(User.objects.get(username="guardian@example.com").email, "guardian@example.com")

    def test_each_logs_in_with_the_default_password_and_lands_on_its_page(self):
        for username, home in [("admin@example.com", "analytics"), ("guardian@example.com", "overview"), ("child@example.com", "board")]:
            response = self.client.post(reverse("login"), {"username": username, "password": PASSWORD})
            self.assertRedirects(response, reverse(home), fetch_redirect_response=False, msg_prefix=username)
            self.client.post(reverse("logout"))
