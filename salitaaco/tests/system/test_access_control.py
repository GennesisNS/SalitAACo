from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.forms.system.add_admin import AddAdminForm
from salitaaco.forms.system.remove_admin import RemoveAdminForm
from salitaaco.models.admin_account import AdminAccount
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.perms_check import is_administrator

# A guardian's pages with no child in their address, each its own sidebar item.
GUARDIAN_PAGES = {"overview", "children", "family_voices", "guardian_words", "plan", "support"}

NEW_ADMIN = {
    "display_name": "Juan Dela Cruz",
    "username": "juan",
    "password": "Lihim#2026",
    "confirm_password": "Lihim#2026",
}


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


def navigation_of(response):
    return {item["id"] for category in response.context["navigation_items"] for item in category["items"]}


class AccessControlTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.url = reverse("system_access")

    def test_add_admin_form_asks_for_a_new_account(self):
        errors = AddAdminForm({}).errors
        self.assertEqual(errors["display_name"], ["Ilagay ang pangalan ng admin."])
        self.assertEqual(errors["username"], ["Ilagay ang username."])

        # An existing account, a guardian's included, is never made an admin.
        for taken in ["nanay", "NANAY", "developer"]:
            form = AddAdminForm({**NEW_ADMIN, "username": taken})
            self.assertEqual(form.errors["username"], ["Ginagamit na ang username na ito."], taken)

        self.assertIn("password", AddAdminForm({**NEW_ADMIN, "password": "maikli", "confirm_password": "maikli"}).errors)
        self.assertEqual(AddAdminForm({**NEW_ADMIN, "confirm_password": "Iba#2026"}).errors["confirm_password"],
                         ["Hindi magkatugma ang password at kumpirmasyon."])
        self.assertTrue(AddAdminForm(NEW_ADMIN).is_valid())

    def test_an_admin_cannot_remove_themselves(self):
        form = RemoveAdminForm({}, acting_user=self.developer, target_user=self.developer)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["Hindi mo mabubura ang sarili mong admin account dito."])
        self.assertTrue(RemoveAdminForm({}, acting_user=self.developer, target_user=self.miguel).is_valid())

    def test_only_admins_open_the_page_and_change_who_is_one(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.assertEqual(self.client.post(self.url, NEW_ADMIN).status_code, 302)
            self.assertEqual(self.client.post(reverse("remove_admin", args=[self.developer.pk])).status_code, 302)
        self.assertFalse(User.objects.filter(username="juan").exists())
        self.assertTrue(is_administrator(self.developer))

    def test_page_lists_the_admins(self):
        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertEqual([admin.username for admin in response.context["admins"]], ["developer"])
        self.assertContains(response, "Ikaw ito")
        self.assertContains(response, "<th>Aksyon</th>")

    def test_making_an_admin_makes_a_new_account_of_its_own(self):
        self.login_as("developer")
        response = self.client.post(self.url, NEW_ADMIN)

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Nagawa na ang admin account na @juan."])
        juan = User.objects.get(username="juan")
        self.assertTrue(is_administrator(juan))
        self.assertEqual(AdminAccount.objects.get(user=juan).display_name, "Juan Dela Cruz")
        self.assertFalse(GuardianAccount.objects.filter(user=juan).exists())
        self.assertEqual(list(juan.groups.values_list("name", flat=True)), ["Administrator"])
        self.assertFalse(juan.is_staff or juan.is_superuser)
        # Nanay is as she was.
        self.assertFalse(is_administrator(self.nanay.user))
        self.assertEqual([admin.username for admin in self.client.get(self.url).context["admins"]], ["developer", "juan"])

        # The new admin logs in to the admin's pages, and only those.
        self.client.post(reverse("logout"))
        response = self.client.post(reverse("login"), {"username": "juan", "password": "Lihim#2026"})
        self.assertRedirects(response, reverse("analytics"))
        navigation = navigation_of(self.client.get(reverse("analytics")))
        self.assertIn("users", navigation)
        self.assertTrue(navigation.isdisjoint(GUARDIAN_PAGES), navigation & GUARDIAN_PAGES)
        for route in GUARDIAN_PAGES:
            self.assertEqual(self.client.get(reverse(route)).status_code, 302, route)

    def test_a_form_that_is_not_valid_reopens_and_makes_nothing(self):
        self.login_as("developer")
        response = self.client.post(self.url, {**NEW_ADMIN, "username": "nanay"})
        self.assertContains(response, "Ginagamit na ang username na ito.")
        self.assertContains(response, 'data-modal="add-admin" data-open="true"')
        self.assertFalse(is_administrator(self.nanay.user))
        self.assertFalse(AdminAccount.objects.filter(user=self.nanay.user).exists())

    def test_removing_an_admin_deletes_their_account(self):
        self.login_as("developer")
        self.client.post(self.url, NEW_ADMIN)
        juan = User.objects.get(username="juan")
        remove_url = reverse("remove_admin", args=[juan.pk])
        self.assertEqual(self.client.get(remove_url).status_code, 405)

        response = self.client.post(remove_url)

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response)[-1], "Nabura na ang admin account na @juan.")
        self.assertFalse(User.objects.filter(username="juan").exists())
        self.assertFalse(AdminAccount.objects.filter(display_name="Juan Dela Cruz").exists())
        self.assertFalse(self.client.login(username="juan", password="Lihim#2026"))
        # Only an admin's account can be deleted here.
        self.assertEqual(self.client.post(reverse("remove_admin", args=[self.nanay.user.pk])).status_code, 404)
        self.assertTrue(User.objects.filter(username="nanay").exists())

    def test_an_admin_cannot_delete_their_own_account_here(self):
        self.login_as("developer")
        response = self.client.post(reverse("remove_admin", args=[self.developer.pk]))
        self.assertEqual(messages_of(response), ["Hindi mo mabubura ang sarili mong admin account dito."])
        self.assertTrue(is_administrator(self.developer))
        self.assertNotContains(self.client.get(self.url), f'data-modal="remove-admin-{self.developer.pk}"')

    def test_a_leftover_guardian_group_never_gives_an_admin_the_guardians_pages(self):
        self.developer.groups.add(Group.objects.get(name="Guardian"))
        self.login_as("developer")
        self.assertTrue(navigation_of(self.client.get(reverse("analytics"))).isdisjoint(GUARDIAN_PAGES))
        self.assertEqual(self.client.get(reverse("overview")).status_code, 302)
