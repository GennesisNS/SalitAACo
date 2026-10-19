from django.test import SimpleTestCase
from django.urls import reverse

from salitaaco.defaults.plans import APPROVED, FREE, PENDING, PLUS, REJECTED
from salitaaco.forms.revenue.reject_payment import RejectPaymentForm
from salitaaco.forms.revenue.transaction_status import ALL_STATUSES, TransactionStatusForm
from salitaaco.tests.payments_base import make_payment, messages_of
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.plans import current_plan


class RevenueFormsTest(SimpleTestCase):
    def test_no_status_or_an_unknown_one_means_all_of_them(self):
        for data in [None, {}, {"status": ""}, {"status": "wala-nito"}]:
            self.assertEqual(TransactionStatusForm(data).chosen(), ALL_STATUSES, data)

    def test_a_real_status_is_kept(self):
        for status in [PENDING, APPROVED, REJECTED]:
            self.assertEqual(TransactionStatusForm({"status": status}).chosen(), status)

    def test_rejecting_needs_a_reason(self):
        self.assertEqual(RejectPaymentForm({}).errors["note"], ["Ilagay kung bakit tinanggihan ang bayad."])
        self.assertEqual(
            RejectPaymentForm({"note": "a" * 301}).errors["note"],
            ["Masyadong mahaba ang dahilan (hanggang 300 character)."],
        )
        self.assertTrue(RejectPaymentForm({"note": "Malabo ang larawan."}).is_valid())


class RevenueBase(UserBase):
    url = reverse("revenue")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben")


class RevenuePageTest(RevenueBase):
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
        self.assertContains(response, "Mali ang halaga.")

        # An unknown status shows them all.
        self.assertEqual(len(self.client.get(self.url, {"status": "wala-nito"}).context["payments"]), 3)

    def test_only_a_waiting_payment_has_the_buttons(self):
        waiting = make_payment(self.tatay)
        make_payment(self.nanay, status=APPROVED)

        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertContains(response, f'data-open-modal="approve-{waiting.uuid}">Aprubahan</button>', count=1)
        self.assertContains(response, f'data-open-modal="reject-{waiting.uuid}">Tanggihan</button>', count=1)
        self.assertContains(response, f'action="{reverse("approve_payment", args=[waiting.uuid])}"', count=1)
        self.assertContains(response, f'action="{reverse("reject_payment", args=[waiting.uuid])}"', count=1)
        self.assertContains(response, 'data-open-modal="proof"', count=2)
        self.assertContains(response, reverse("view_payment_proof", args=[waiting.uuid]))


class ApproveAndRejectTest(RevenueBase):
    def test_approving_puts_the_guardian_on_the_plan(self):
        payment = make_payment(self.nanay)
        self.login_as("developer")
        response = self.client.post(reverse("approve_payment", args=[payment.uuid]), {"next": "?status=pending"})

        self.assertRedirects(response, f"{self.url}?status=pending")
        self.assertEqual(messages_of(response), ["Naaprubahan na. Naka-SalitAACo Plus na si Nanay Rosa."])
        payment.refresh_from_db()
        self.assertEqual((payment.status, payment.reviewed_by), (APPROVED, self.developer))
        self.assertEqual(current_plan(self.nanay).key, PLUS)

        # Approving it again changes nothing.
        response = self.client.post(reverse("approve_payment", args=[payment.uuid]))
        self.assertEqual(messages_of(response), ["Hindi na naghihintay ang bayad na ito."])

    def test_rejecting_needs_a_reason_and_keeps_the_guardian_on_free(self):
        payment = make_payment(self.nanay)
        self.login_as("developer")
        url = reverse("reject_payment", args=[payment.uuid])

        response = self.client.post(url, {"note": ""})
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Ilagay kung bakit tinanggihan ang bayad."])
        payment.refresh_from_db()
        self.assertEqual(payment.status, PENDING)

        response = self.client.post(url, {"note": "Malabo ang larawan."})
        self.assertEqual(messages_of(response), ["Tinanggihan ang bayad ni Nanay Rosa."])
        payment.refresh_from_db()
        self.assertEqual((payment.status, payment.note), (REJECTED, "Malabo ang larawan."))
        self.assertEqual(current_plan(self.nanay).key, FREE)

    def test_only_admins_approve_or_reject_and_only_by_post(self):
        payment = make_payment(self.nanay)
        for route in ["approve_payment", "reject_payment"]:
            url = reverse(route, args=[payment.uuid])
            self.login_as("nanay")
            self.assertEqual(self.client.post(url, {"note": "x"}).status_code, 302)
            self.login_as("developer")
            self.assertEqual(self.client.get(url).status_code, 405)
        payment.refresh_from_db()
        self.assertEqual(payment.status, PENDING)

    def test_the_way_back_stays_on_this_page(self):
        payment = make_payment(self.nanay)
        self.login_as("developer")
        response = self.client.post(reverse("approve_payment", args=[payment.uuid]), {"next": "https://iba.example/"})
        self.assertRedirects(response, self.url)
