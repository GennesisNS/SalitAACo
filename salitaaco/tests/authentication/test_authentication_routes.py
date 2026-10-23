import importlib
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError
from django.test import RequestFactory, override_settings
from django.urls import clear_url_caches, resolve, reverse
from django.utils.functional import SimpleLazyObject

from salitaaco import urls
from salitaaco.models.admin_account import AdminAccount
from salitaaco.routes import error_handler
from salitaaco.models.child_account import ChildAccount
from salitaaco.tests.users_base import GUARDIAN_PASSWORD, UserBase, make_guardian
from salitaaco.utils.account import find_user_account


class LoginRouteTest(UserBase):
    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mag-log in")

    def test_login_redirects_to_the_board(self):
        response = self.client.post(reverse("login"), {"username": "miguel", "password": "lihim1234"})
        self.assertRedirects(response, reverse("board"))

    def test_each_kind_of_account_lands_on_its_own_first_page(self):
        make_guardian("nanay", "Nanay Rosa")
        landings = [
            ("miguel", "lihim1234", "board"),
            ("nanay", GUARDIAN_PASSWORD, "overview"),
            ("developer", "dev-password", "analytics"),
        ]
        for username, password, route in landings:
            response = self.client.post(reverse("login"), {"username": username, "password": password})
            self.assertRedirects(response, reverse(route), msg_prefix=username)
            # Already logged in, the login and sign-up pages and the site's root lead there too.
            for page in ["login", "register", "index"]:
                self.assertRedirects(self.client.get(reverse(page)), reverse(route), msg_prefix=f"{username} {page}")
            self.client.post(reverse("logout"))

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

    def test_index_is_the_public_website_or_the_board(self):
        # Nobody logged in: the public website (the public/ app), which leads to logging in.
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{reverse("login")}"')
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

    def test_a_server_error_has_its_page_even_when_the_database_fails(self):
        # The page is drawn without the context processors, which would read the database again:
        # here, looking up who is logged in fails as it would with the database down.
        def database_down():
            raise DatabaseError("the database is down")

        request = RequestFactory().get("/kahit-saan/")
        request.user = SimpleLazyObject(database_down)
        response = error_handler.server_error(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn("May problema sa server", response.content.decode())
        self.assertIn('href="/"', response.content.decode())


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
    PASSWORD = "Lihim#2026"

    def make_admin(self, *args, passwords=(PASSWORD, PASSWORD)):
        """Run the command, typing `passwords` when it asks."""
        with mock.patch("salitaaco.management.commands.make_admin.getpass.getpass", side_effect=list(passwords)):
            output = StringIO()
            call_command("make_admin", *args, stdout=output)
            return output.getvalue()

    def test_makes_a_new_admin_account_of_its_own(self):
        output = self.make_admin("juan", "--name", "Juan Dela Cruz")

        self.assertIn("Made the admin account juan.", output)
        juan = User.objects.get(username="juan")
        self.assertIsInstance(find_user_account(juan), AdminAccount)
        self.assertEqual(juan.admin_account.display_name, "Juan Dela Cruz")
        self.assertEqual(list(juan.groups.values_list("name", flat=True)), ["Administrator"])
        self.assertFalse(juan.is_staff or juan.is_superuser)
        self.assertTrue(self.client.login(username="juan", password=self.PASSWORD))

    def test_an_existing_account_is_never_made_an_admin(self):
        make_guardian("nanay", "Nanay Rosa")
        for taken in ["nanay", "Miguel", "developer"]:
            with self.assertRaisesRegex(CommandError, "is taken"):
                self.make_admin(taken)
        nanay = User.objects.get(username="nanay")
        self.assertFalse(AdminAccount.objects.filter(user=nanay).exists())
        self.assertIsInstance(find_user_account(User.objects.get(username="miguel")), ChildAccount)

    def test_the_password_is_checked(self):
        with self.assertRaisesRegex(CommandError, "do not match"):
            self.make_admin("juan", passwords=(self.PASSWORD, "Iba#2026"))
        with self.assertRaisesRegex(CommandError, "Hindi bababa sa 8 character ang password."):
            self.make_admin("juan", passwords=("maikli", "maikli"))
        with self.assertRaisesRegex(CommandError, "walang espasyo"):
            self.make_admin("juan dela cruz")
        self.assertFalse(User.objects.filter(username__startswith="juan").exists())

    def test_the_password_can_come_from_the_environment(self):
        with mock.patch.dict("os.environ", {"ADMIN_PASSWORD": self.PASSWORD}):
            self.make_admin("juan", passwords=())
        self.assertTrue(self.client.login(username="juan", password=self.PASSWORD))

    def test_staff_flag_also_opens_the_django_admin_site(self):
        self.make_admin("juan", "--staff")
        juan = User.objects.get(username="juan")
        self.assertTrue(juan.is_staff and juan.is_superuser)

    def test_remove_deletes_an_admin_account_and_nothing_else(self):
        self.make_admin("juan")
        self.assertIn("Deleted the admin account juan.", self.make_admin("juan", "--remove"))
        self.assertFalse(User.objects.filter(username="juan").exists())

        for not_an_admin in ["miguel", "wala"]:
            with self.assertRaisesRegex(CommandError, "No admin account"):
                self.make_admin(not_an_admin, "--remove")
        self.assertTrue(User.objects.filter(username="miguel").exists())
