from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from salitaaco.defaults.payment_examples import EXAMPLE_TRANSACTIONS
from salitaaco.defaults.plans import APPROVED, FREE, PAYMENT_STATUSES, PENDING, PLANS, PLUS, REJECTED
from salitaaco.tests.users_base import UserBase, make_guardian


class PlanDefaultsTest(SimpleTestCase):
    def test_the_two_starting_plans_and_their_prices(self):
        self.assertEqual(
            [(plan["key"], plan["name"], plan["price"], plan["offered"]) for plan in PLANS],
            [(FREE, "Free", 0, True), (PLUS, "SalitAACo Plus", 149, True)],
        )
        for plan in PLANS:
            self.assertTrue(plan["features"], plan["key"])

    def test_the_examples_cover_every_status_and_say_they_are_examples(self):
        self.assertEqual({row["status"] for row in EXAMPLE_TRANSACTIONS}, {PENDING, APPROVED, REJECTED})
        self.assertEqual([status for status, name in PAYMENT_STATUSES], [PENDING, APPROVED, REJECTED])
        for row in EXAMPLE_TRANSACTIONS:
            self.assertTrue(row["reference"].startswith("HALIMBAWA"))
            self.assertIn("alimbawa", row["guardian"])


class PlanBase(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])


class PlanPageTest(PlanBase):
    def test_only_guardians_open_the_plan_pages(self):
        for route in ["plan", "plan_transactions"]:
            url = reverse(route)
            self.assertRedirects(self.client.get(url), f"/login/?next={url}")
            for username in ["miguel", "developer"]:
                self.login_as(username)
                self.assertEqual(self.client.get(url).status_code, 302, f"{username} {route}")
            self.login_as("nanay")
            self.assertEqual(self.client.get(url).status_code, 200, route)
            self.client.post(reverse("logout"))

    def test_page_shows_both_plans_and_the_free_one_as_current(self):
        self.login_as("nanay")
        response = self.client.get(reverse("plan"))

        self.assertEqual(response.context["current_plan"]["key"], FREE)
        self.assertEqual(
            [(plan["key"], plan["is_current"], plan["needs_payment"]) for plan in response.context["plans"]],
            [(FREE, True, False), (PLUS, False, True)],
        )
        self.assertContains(response, "₱0")
        self.assertContains(response, "₱149")
        self.assertContains(response, "Kunin ang SalitAACo Plus")
        self.assertContains(response, f'href="{reverse("plan_transactions")}"')

    def test_paying_is_a_qr_code_and_an_upload_that_does_not_send_yet(self):
        self.login_as("nanay")
        response = self.client.get(reverse("plan"))

        self.assertContains(response, 'data-modal="pay"')
        self.assertContains(response, '<figure class="qrCode">')
        self.assertContains(response, "Hindi pa ito mababayaran.")
        self.assertContains(response, '<input type="file" id="proofFile" accept="image/jpeg,image/png,image/webp" />')
        self.assertContains(response, "hanggang 5 MB")
        # Frontend only: the button that would send the proof is disabled, and the page says why.
        self.assertContains(response, '<button class="primaryBtn" type="button" disabled>Ipadala ang patunay ng bayad</button>')
        self.assertContains(response, "Hindi pa gumagana ang pagpapadala")
        # Nothing on the page posts anywhere but the sidebar's log out.
        self.assertContains(response, 'method="post"', count=1)

    def test_posting_to_the_plan_pages_changes_nothing(self):
        self.login_as("nanay")
        for route in ["plan", "plan_transactions"]:
            self.assertEqual(self.client.post(reverse(route), {"plan": PLUS}).status_code, 200)
        self.assertEqual(self.client.get(reverse("plan")).context["current_plan"]["key"], FREE)

    def test_the_sidebar_and_the_overview_lead_to_the_plan(self):
        self.login_as("nanay")
        response = self.client.get(reverse("overview"))
        self.assertContains(response, f'href="{reverse("plan")}"', count=2)
        self.assertContains(response, "Kasalukuyang plano: <b>Free</b>")

        items = {
            item["id"]: item for category in self.client.get(reverse("plan_transactions")).context["navigation_items"]
            for item in category["items"]
        }
        self.assertTrue(items["plan"]["active"])


class TransactionHistoryTest(PlanBase):
    def test_history_is_empty_because_nothing_is_saved_yet(self):
        self.login_as("nanay")
        response = self.client.get(reverse("plan_transactions"))

        self.assertEqual(response.context["transactions"], [])
        self.assertContains(response, "Wala ka pang bayad.")
        self.assertNotContains(response, "<table>")

    def test_examples_are_never_shown_on_a_live_site(self):
        # DEBUG is off in tests, as it is in production.
        self.login_as("nanay")
        response = self.client.get(reverse("plan_transactions"), {"halimbawa": "1"})

        self.assertEqual(response.context["transactions"], [])
        self.assertNotContains(response, "HALIMBAWA")
        self.assertNotContains(response, "Ipakita ang halimbawa")

    @override_settings(DEBUG=True)
    def test_in_development_the_examples_show_when_asked_for_and_say_what_they_are(self):
        self.login_as("nanay")
        response = self.client.get(reverse("plan_transactions"))
        self.assertEqual(response.context["transactions"], [])
        self.assertContains(response, "Ipakita ang halimbawa")

        response = self.client.get(reverse("plan_transactions"), {"halimbawa": "1"})
        self.assertEqual(
            [(row["status"], row["status_name"]) for row in response.context["transactions"]],
            [(PENDING, "Naghihintay"), (APPROVED, "Aprubado"), (REJECTED, "Tinanggihan")],
        )
        self.assertContains(response, "Halimbawa lang ang mga bayad sa ibaba.")
        for status in [PENDING, APPROVED, REJECTED]:
            self.assertContains(response, f'<span class="statusBadge {status}">')
        self.assertContains(response, "Malabo ang larawan ng bayad.")
