from django.test import SimpleTestCase
from django.urls import reverse

from salitaaco.defaults.plans import APPROVED, PENDING, REJECTED
from salitaaco.forms.revenue.transaction_status import ALL_STATUSES, TransactionStatusForm
from salitaaco.tests.payments_base import make_payment
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.plans import approve_payment


class TransactionStatusFormTest(SimpleTestCase):
    def test_no_status_or_an_unknown_one_means_all_of_them(self):
        for data in [None, {}, {"status": ""}, {"status": "wala-nito"}]:
            self.assertEqual(TransactionStatusForm(data).chosen(), ALL_STATUSES, data)

    def test_a_real_status_is_kept(self):
        for status in [PENDING, APPROVED, REJECTED]:
            self.assertEqual(TransactionStatusForm({"status": status}).chosen(), status)


class RevenuePageTest(UserBase):
    """Kita: the record of every payment and what became of it, to look at only."""
    url = reverse("revenue")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben")

    def tabs(self, response):
        return [(tab["label"], tab["count"], tab["active"]) for tab in response.context["tabs"]]

    def test_only_admins_open_the_page(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
        self.login_as("developer")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_page_is_empty_before_the_first_payment(self):
        self.login_as("developer")
        response = self.client.get(self.url)

        self.assertEqual(self.tabs(response), [
            ("Lahat", 0, True), ("Naghihintay", 0, False), ("Aprubado", 0, False), ("Tinanggihan", 0, False),
        ])
        self.assertContains(response, "Walang bayad sa status na ito.")
        self.assertNotContains(response, "<table>")
        # The page is in the sidebar and lit there.
        self.assertContains(response, f'<a class="sidebarItem active" href="{self.url}" aria-current="page">')

    def test_the_tabs_count_and_filter_by_status(self):
        make_payment(self.nanay, status=APPROVED)
        make_payment(self.nanay, status=REJECTED, note="Mali ang halaga.")
        make_payment(self.tatay)

        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertEqual(self.tabs(response), [
            ("Lahat", 3, True), ("Naghihintay", 1, False), ("Aprubado", 1, False), ("Tinanggihan", 1, False),
        ])
        self.assertEqual(len(response.context["payments"]), 3)
        self.assertContains(response, 'href="?status=pending"')

        response = self.client.get(self.url, {"status": "rejected"})
        self.assertEqual([payment.status for payment in response.context["payments"]], [REJECTED])

        # An unknown status shows them all.
        self.assertEqual(len(self.client.get(self.url, {"status": "wala-nito"}).context["payments"]), 3)

    def test_it_only_shows_payments_with_their_proof_and_the_time_they_bought(self):
        waiting = make_payment(self.tatay)
        approved = make_payment(self.nanay)
        approve_payment(approved, self.developer)
        approved.refresh_from_db()

        self.login_as("developer")
        response = self.client.get(self.url)
        for column in ["Petsa", "Tagapag-alaga", "Plano", "Halaga", "Status", "Patunay", "Sakop"]:
            self.assertContains(response, f"<th>{column}</th>")
        self.assertNotContains(response, "<th>Aksyon</th>")
        # Approving and rejecting are on Mga Subscription, not here.
        for gone in ["Aprubahan", "Tanggihan", 'name="reject_form"', reverse("approve_payment", args=[waiting.uuid])]:
            self.assertNotContains(response, gone)
        self.assertContains(response, f'href="{reverse("subscriptions")}"')

        self.assertContains(response, 'data-open-modal="proof"', count=2)
        self.assertContains(response, reverse("view_payment_proof", args=[waiting.uuid]))
        self.assertContains(response, f'{approved.starts_at:%Y-%m-%d} hanggang {approved.ends_at:%Y-%m-%d}')

    def test_posting_changes_nothing(self):
        payment = make_payment(self.nanay)
        self.login_as("developer")
        self.client.post(self.url, {"reject_form": "", "payment": payment.uuid, "note": "Malabo."})
        payment.refresh_from_db()
        self.assertEqual(payment.status, PENDING)
