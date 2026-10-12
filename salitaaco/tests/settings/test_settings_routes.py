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

    def sidebar_items(self, route):
        return {
            item["id"]: item
            for category in self.client.get(reverse(route)).context["navigation_items"]
            for item in category["items"]
        }

    def test_sidebar_lists_settings_and_highlights_it_when_open(self):
        self.login_as("developer")
        self.assertTrue(self.sidebar_items("settings")["settings"]["active"])
        self.assertFalse(self.sidebar_items("profile")["settings"]["active"])

    def test_a_child_reaches_settings_from_the_profile_page(self):
        self.login_as("miguel")
        self.assertNotIn("settings", self.sidebar_items("board"))
        self.assertContains(self.client.get(reverse("profile")), f'href="{reverse("settings")}"')

    def test_profile_is_in_a_childs_navigation_and_behind_the_avatar_for_everyone(self):
        # A child has Profile along the bottom; the sidebar of the others does not list it.
        self.login_as("miguel")
        self.assertTrue(self.sidebar_items("profile")["profile"]["active"])
        self.login_as("developer")
        self.assertNotIn("profile", self.sidebar_items("settings"))

        # The avatar link is in both layouts, so it is on every page drawn in the user's own layout.
        pages = {"miguel": ["board", "settings", "profile"], "developer": ["settings", "profile"]}
        for username, routes in pages.items():
            self.login_as(username)
            for route in routes:
                response = self.client.get(reverse(route))
                self.assertContains(response, f'<a href="{reverse("profile")}" class="accountLink"')
