from django.urls import reverse

from salitaaco.tests.users_base import UserBase


class SettingsAccessTest(UserBase):
    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(reverse("settings"))
        self.assertRedirects(response, f"/login/?next={reverse('settings')}")

    def test_every_role_sees_the_page(self):
        for username in ["miguel", "developer"]:
            self.login_as(username)
            response = self.client.get(reverse("settings"))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Pag-edit ng mga Tile / Cell")
            self.assertContains(response, 'id="darkToggle"')


class SettingsAndProfileAreSeparatePagesTest(UserBase):
    def test_settings_has_no_account_forms(self):
        self.login_as("miguel")
        response = self.client.get(reverse("settings"))
        self.assertNotContains(response, "Impormasyon ng Account")
        self.assertNotContains(response, "Burahin ang Account")

    def test_profile_has_the_account_forms_and_no_settings(self):
        self.login_as("miguel")
        response = self.client.get(reverse("profile"))
        for text in ["Impormasyon ng Account", "Palitan ang Password", "Burahin ang Account"]:
            self.assertContains(response, text)
        self.assertNotContains(response, "Pag-edit ng mga Tile / Cell")
        self.assertNotContains(response, 'id="darkToggle"')

    def test_sidebar_lists_both_and_highlights_the_open_one(self):
        self.login_as("miguel")
        for route, other in [("profile", "settings"), ("settings", "profile")]:
            items = {
                item["id"]: item
                for category in self.client.get(reverse(route)).context["navigation_items"]
                for item in category["items"]
            }
            self.assertEqual(items[route]["name"], route.title())
            self.assertTrue(items[route]["active"])
            self.assertFalse(items[other]["active"])
