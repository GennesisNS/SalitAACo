import importlib
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.urls import clear_url_caches, resolve, reverse

from salitaaco import urls
from salitaaco.models.admin_account import AdminAccount
from salitaaco.models.child_account import ChildAccount
from salitaaco.tests.users_base import UserBase
from salitaaco.utils.account import find_user_account


class LoginRouteTest(UserBase):
    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mag-log in")

    def test_login_redirects_to_the_board(self):
        response = self.client.post(reverse("login"), {"username": "miguel", "password": "lihim1234"})
        self.assertRedirects(response, reverse("board"))

    def test_login_ignores_username_case(self):
        response = self.client.post(reverse("login"), {"username": "MIGUEL", "password": "lihim1234"})
        self.assertRedirects(response, reverse("board"))

    def test_login_follows_next(self):
        self.client.post(
            reverse("login"),
            {"username": "developer", "password": "dev-password", "next": reverse("analytics")},
        )
        response = self.client.get(reverse("analytics"))
        self.assertEqual(response.status_code, 200)

    def test_login_ignores_next_on_another_site(self):
        response = self.client.post(
            reverse("login"),
            {"username": "miguel", "password": "lihim1234", "next": "https://example.com/"},
        )
        self.assertRedirects(response, reverse("board"))

    def test_wrong_password_shows_the_error(self):
        response = self.client.post(reverse("login"), {"username": "miguel", "password": "mali"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Maling username o password.")

    def test_unknown_username_shows_the_same_error(self):
        response = self.client.post(reverse("login"), {"username": "wala", "password": "lihim1234"})
        self.assertContains(response, "Maling username o password.")

    def test_login_records_last_login(self):
        self.client.post(reverse("login"), {"username": "miguel", "password": "lihim1234"})
        self.assertIsNotNone(User.objects.get(username="miguel").last_login)

    def test_logged_in_user_is_sent_to_the_board(self):
        self.login_as("miguel")
        self.assertRedirects(self.client.get(reverse("login")), reverse("board"))
        self.assertRedirects(self.client.get(reverse("register")), reverse("board"))


class RegisterRouteTest(UserBase):
    def test_register_creates_a_guardian_account_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {"display_name": "Bagong Magulang", "username": "bago", "password": "Bagong#123", "confirm_password": "Bagong#123"},
        )
        # A new guardian lands on the page where they add their children.
        self.assertRedirects(response, reverse("children"))

        user = User.objects.get(username="bago")
        self.assertTrue(user.check_password("Bagong#123"))
        self.assertEqual(user.guardian_account.display_name, "Bagong Magulang")
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Guardian"])
        self.assertFalse(ChildAccount.objects.filter(user=user).exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_register_with_passwords_that_differ_shows_the_error(self):
        response = self.client.post(
            reverse("register"),
            {"display_name": "Bagong Magulang", "username": "bago", "password": "Bagong#123", "confirm_password": "Iba#12345"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hindi magkatugma ang password at kumpirmasyon.")
        self.assertFalse(User.objects.filter(username="bago").exists())

    def test_register_with_a_taken_username_shows_the_error(self):
        response = self.client.post(
            reverse("register"),
            {"display_name": "Isa Pa", "username": "Miguel", "password": "Bagong#123", "confirm_password": "Bagong#123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ginagamit na ang username na ito.")
        self.assertEqual(User.objects.filter(username__iexact="miguel").count(), 1)


class LogoutAndRedirectsTest(UserBase):
    def test_logout_needs_post(self):
        self.login_as("miguel")
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_logout_ends_the_session(self):
        self.login_as("miguel")
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_index_goes_to_login_or_board(self):
        self.assertRedirects(self.client.get(reverse("index")), reverse("login"))
        self.login_as("miguel")
        self.assertRedirects(self.client.get(reverse("index")), reverse("board"))

    def test_home_address_of_the_php_application_redirects(self):
        self.login_as("miguel")
        for old_address in ["/home", "/home/"]:
            self.assertRedirects(self.client.get(old_address), reverse("board"))

    def test_unknown_address_uses_the_error_page(self):
        response = self.client.get("/walang-ganito/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Walang ganitong pahina", status_code=404)


class AdminAddressTest(UserBase):
    """/admin is Django's admin site when SHOW_ADMIN_ROUTES is on, and the old PHP address otherwise."""

    def show_admin_routes(self, enabled):
        # The URL patterns are built when salitaaco.urls is imported, so it is
        # reloaded under the changed setting and again once the test is over.
        override = override_settings(SHOW_ADMIN_ROUTES=enabled)
        override.enable()
        importlib.reload(urls)
        clear_url_caches()

        def restore():
            override.disable()
            importlib.reload(urls)
            clear_url_caches()

        self.addCleanup(restore)

    def test_admin_redirects_to_the_dashboard_when_the_admin_site_is_off(self):
        self.show_admin_routes(False)
        self.login_as("developer")
        for old_address in ["/admin", "/admin/"]:
            self.assertRedirects(self.client.get(old_address), reverse("analytics"))

    def test_admin_is_the_django_admin_site_when_it_is_on(self):
        self.show_admin_routes(True)
        self.assertEqual(resolve("/admin/").app_name, "admin")

        # The app's Administrator group does not open Django's admin site; staff status does.
        self.login_as("developer")
        self.assertRedirects(self.client.get("/admin/"), "/admin/login/?next=/admin/")

        User.objects.filter(pk=self.developer.pk).update(is_staff=True, is_superuser=True)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

        # The app's own dashboard is unaffected.
        self.assertEqual(self.client.get(reverse("analytics")).status_code, 200)


class MakeAdminCommandTest(UserBase):
    def is_admin(self, username):
        return User.objects.get(username=username).groups.filter(name="Administrator").exists()

    def test_grants_and_removes_admin_access(self):
        call_command("make_admin", "Miguel", stdout=StringIO())
        self.assertTrue(self.is_admin("miguel"))

        call_command("make_admin", "miguel", "--remove", stdout=StringIO())
        self.assertFalse(self.is_admin("miguel"))

    def test_admin_account_is_added_beside_the_existing_one(self):
        call_command("make_admin", "miguel", stdout=StringIO())
        miguel = User.objects.get(username="miguel")
        self.assertEqual(miguel.admin_account.display_name, "Miguel")
        self.assertEqual(miguel.child_account.age, 7)
        self.assertIsInstance(find_user_account(miguel), AdminAccount)

        # Running it again changes nothing.
        call_command("make_admin", "miguel", stdout=StringIO())
        self.assertEqual(AdminAccount.objects.filter(user=miguel).count(), 1)

        call_command("make_admin", "miguel", "--remove", stdout=StringIO())
        miguel = User.objects.get(username="miguel")
        self.assertFalse(AdminAccount.objects.filter(user=miguel).exists())
        self.assertIsInstance(find_user_account(miguel), ChildAccount)

    def test_staff_flag_also_opens_the_django_admin_site(self):
        call_command("make_admin", "miguel", stdout=StringIO())
        miguel = User.objects.get(username="miguel")
        self.assertFalse(miguel.is_staff or miguel.is_superuser)

        call_command("make_admin", "miguel", "--staff", stdout=StringIO())
        miguel = User.objects.get(username="miguel")
        self.assertTrue(self.is_admin("miguel") and miguel.is_staff and miguel.is_superuser)

        call_command("make_admin", "miguel", "--remove", stdout=StringIO())
        miguel = User.objects.get(username="miguel")
        self.assertFalse(self.is_admin("miguel") or miguel.is_staff or miguel.is_superuser)

    def test_unknown_username_fails(self):
        with self.assertRaises(CommandError):
            call_command("make_admin", "wala", stdout=StringIO())
