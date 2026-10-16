from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.forms.system.add_admin import AddAdminForm
from salitaaco.forms.system.remove_admin import RemoveAdminForm
from salitaaco.models.admin_account import AdminAccount
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.tests.users_base import GUARDIAN_PASSWORD, UserBase, make_guardian
from salitaaco.utils.perms_check import is_administrator


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class AccessControlTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.url = reverse("system_access")

    def test_add_admin_form(self):
        self.assertEqual(AddAdminForm({}).errors["username"], ["Ilagay ang username."])
        self.assertEqual(AddAdminForm({"username": "wala"}).errors["username"], ["Walang account na may ganitong username."])
        self.assertEqual(AddAdminForm({"username": "Developer"}).errors["username"], ["Admin na ang account na ito."])
        User.objects.filter(pk=self.ana.pk).update(is_active=False)
        self.assertEqual(AddAdminForm({"username": "ana"}).errors["username"], ["Hindi aktibo ang account na ito."])

        form = AddAdminForm({"username": " NANAY "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.user, self.nanay.user)

    def test_an_admin_cannot_remove_themselves(self):
        form = RemoveAdminForm({}, acting_user=self.developer, target_user=self.developer)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["Hindi mo maaalis ang sarili mong admin access."])
        self.assertTrue(RemoveAdminForm({}, acting_user=self.developer, target_user=self.miguel).is_valid())

    def test_only_admins_open_the_page_and_change_who_is_one(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.assertEqual(self.client.post(self.url, {"username": username}).status_code, 302)
            self.assertEqual(self.client.post(reverse("remove_admin", args=[self.developer.pk])).status_code, 302)
        self.assertFalse(is_administrator(self.nanay.user))
        self.assertTrue(is_administrator(self.developer))

    def test_page_lists_the_admins(self):
        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertEqual([admin.username for admin in response.context["admins"]], ["developer"])
        self.assertContains(response, "Ikaw ito")
        self.assertContains(response, "<th>Aksyon</th>")

    def test_giving_admin_access_keeps_what_the_account_already_was(self):
        self.login_as("developer")
        response = self.client.post(self.url, {"username": "nanay"})

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Admin na si @nanay."])
        self.assertTrue(is_administrator(self.nanay.user))
        self.assertTrue(AdminAccount.objects.filter(user=self.nanay.user, display_name="Nanay Rosa").exists())
        # Still a guardian, with her child.
        self.assertEqual(GuardianAccount.objects.get(user=self.nanay.user).children.count(), 1)
        self.assertEqual([admin.username for admin in self.client.get(self.url).context["admins"]], ["developer", "nanay"])

        # She reaches the admin pages now.
        self.client.post(reverse("logout"))
        self.assertTrue(self.client.login(username="nanay", password=GUARDIAN_PASSWORD))
        self.assertEqual(self.client.get(reverse("analytics")).status_code, 200)

    def test_a_username_that_cannot_be_made_admin_reopens_the_form(self):
        self.login_as("developer")
        response = self.client.post(self.url, {"username": "wala"})
        self.assertContains(response, "Walang account na may ganitong username.")
        self.assertContains(response, 'data-modal="add-admin" data-open="true"')

    def test_taking_admin_access_away(self):
        self.login_as("developer")
        self.client.post(self.url, {"username": "nanay"})
        remove_url = reverse("remove_admin", args=[self.nanay.user.pk])
        self.assertEqual(self.client.get(remove_url).status_code, 405)

        response = self.client.post(remove_url)

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response)[-1], "Hindi na admin si @nanay.")
        self.assertFalse(is_administrator(self.nanay.user))
        self.assertFalse(AdminAccount.objects.filter(user=self.nanay.user).exists())
        self.assertTrue(GuardianAccount.objects.filter(user=self.nanay.user).exists())
        # Someone who is not an admin cannot be "removed".
        self.assertEqual(self.client.post(remove_url).status_code, 404)

    def test_an_admin_cannot_remove_their_own_access(self):
        self.login_as("developer")
        response = self.client.post(reverse("remove_admin", args=[self.developer.pk]))
        self.assertEqual(messages_of(response), ["Hindi mo maaalis ang sarili mong admin access."])
        self.assertTrue(is_administrator(self.developer))
        self.assertNotContains(self.client.get(self.url), f'data-modal="remove-admin-{self.developer.pk}"')
