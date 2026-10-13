from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from salitaaco.defaults.plans import APPROVED, PENDING, REJECTED
from salitaaco.forms.revenue.transaction_status import ALL_STATUSES, TransactionStatusForm
from salitaaco.tests.users_base import UserBase, make_guardian


class TransactionStatusFormTest(SimpleTestCase):
    def test_no_status_or_an_unknown_one_means_all_of_them(self):
        for data in [None, {}, {"status": ""}, {"status": "wala-nito"}]:
            self.assertEqual(TransactionStatusForm(data).chosen(), ALL_STATUSES, data)

    def test_a_real_status_is_kept(self):
        for status in [PENDING, APPROVED, REJECTED]:
            self.assertEqual(TransactionStatusForm({"status": status}).chosen(), status)


class RevenuePageTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.url = reverse("revenue")

    def tabs(self, response):
        return [(tab["label"], tab["count"], tab["active"]) for tab in response.context["tabs"]]

    def test_only_admins_open_the_page(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
        self.login_as("developer")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_page_is_empty_because_nothing_is_saved_yet(self):
        self.login_as("developer")
        response = self.client.get(self.url)

        self.assertEqual(response.context["transactions"], [])
        self.assertEqual(self.tabs(response), [
            ("Lahat", 0, True), ("Naghihintay", 0, False), ("Aprubado", 0, False), ("Tinanggihan", 0, False),
        ])
        self.assertContains(response, "Walang bayad sa status na ito.")
        self.assertNotContains(response, "<table>")
        # The page is in the sidebar and lit there.
        self.assertContains(response, f'<a class="sidebarItem active" href="{self.url}" aria-current="page">')

    def test_examples_are_never_shown_on_a_live_site(self):
        self.login_as("developer")
        response = self.client.get(self.url, {"halimbawa": "1"})
        self.assertEqual(response.context["transactions"], [])
        self.assertNotContains(response, "Ipakita ang halimbawa")

    @override_settings(DEBUG=True)
    def test_the_tabs_filter_by_status_and_keep_the_examples_on(self):
        self.login_as("developer")
        response = self.client.get(self.url, {"halimbawa": "1"})
        self.assertEqual(self.tabs(response), [
            ("Lahat", 3, True), ("Naghihintay", 1, False), ("Aprubado", 1, False), ("Tinanggihan", 1, False),
        ])
        self.assertEqual(len(response.context["transactions"]), 3)
        self.assertContains(response, 'href="?halimbawa=1&amp;status=pending"')

        response = self.client.get(self.url, {"halimbawa": "1", "status": "rejected"})
        self.assertEqual([row["status"] for row in response.context["transactions"]], [REJECTED])
        self.assertEqual([tab["label"] for tab in response.context["tabs"] if tab["active"]], ["Tinanggihan"])

        # An unknown status shows them all.
        response = self.client.get(self.url, {"halimbawa": "1", "status": "wala-nito"})
        self.assertEqual(len(response.context["transactions"]), 3)

    @override_settings(DEBUG=True)
    def test_only_a_pending_payment_has_the_buttons_and_they_do_nothing_yet(self):
        self.login_as("developer")
        response = self.client.get(self.url, {"halimbawa": "1"})

        self.assertContains(response, '<button class="primaryBtn smallBtn" type="button" disabled>Aprubahan</button>', count=1)
        self.assertContains(response, '<button class="secondaryBtn danger smallBtn" type="button" disabled>Tanggihan</button>', count=1)
        self.assertContains(response, "Tapos na", count=2)
        self.assertContains(response, 'data-open-modal="proof"', count=3)
        self.assertContains(response, "Hindi pa gumagana ang “Aprubahan” at “Tanggihan”")
