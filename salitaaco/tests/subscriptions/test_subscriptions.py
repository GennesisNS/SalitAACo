from django.urls import reverse

from salitaaco.tests.users_base import UserBase, make_guardian


class SubscriptionsPageTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben")
        cls.url = reverse("subscriptions")

    def test_only_admins_open_the_page(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
        self.login_as("developer")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_every_guardian_counts_as_on_the_free_plan(self):
        self.login_as("developer")
        response = self.client.get(self.url)

        self.assertEqual(
            [(card["label"], card["value"]) for card in response.context["stat_cards"]],
            [("Mga tagapag-alaga", 2), ("Naka-Free", 2), ("Naka-SalitAACo Plus", 0), ("Kita ngayong buwan", "₱0")],
        )
        self.assertEqual([(plan["name"], plan["subscribers"]) for plan in response.context["plans"]],
                         [("Free", 2), ("SalitAACo Plus", 0)])

    def test_the_plans_are_shown_as_a_form_that_cannot_be_used_yet(self):
        self.login_as("developer")
        response = self.client.get(self.url)

        self.assertContains(response, 'id="planName-plus" value="SalitAACo Plus" disabled')
        self.assertContains(response, 'id="planPrice-plus" value="149" min="0" disabled')
        self.assertContains(response, "Boses ng pamilya (family voice banking)\nMada-download na ulat ng paggamit")
        # Whether a plan is offered is a switch, like every other on/off choice.
        self.assertContains(response, '<label class="switch">', count=2)
        self.assertContains(response, 'aria-label="Iniaalok ang Free" checked disabled')
        self.assertContains(response, '<button class="primaryBtn formActions" type="button" disabled>I-save ang plano</button>', count=2)
        self.assertContains(response, "Hindi pa mae-edit ang mga plano")
        self.assertContains(response, 'method="post"', count=1)  # the sidebar's log out only

    def test_the_admin_sidebar_lists_both_pages(self):
        self.login_as("developer")
        items = [
            item["id"] for category in self.client.get(self.url).context["navigation_items"] for item in category["items"]
        ]
        # Side by side, under "Negosyo".
        self.assertEqual(items[items.index("revenue"):items.index("revenue") + 2], ["revenue", "subscriptions"])
