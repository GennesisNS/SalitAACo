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
        payment = "6f1c2b8e-3a4d-4c5e-9f00-112233445566"
        self.assertTrue(RejectPaymentForm({"payment": payment, "note": "Malabo ang larawan."}).is_valid())
        self.assertIn("payment", RejectPaymentForm({"payment": "hindi-uuid", "note": "Malabo ang larawan."}).errors)


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
        self.assertContains(response, f'<input type="hidden" name="payment" value="{waiting.uuid}" />', count=1)
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

    def reject(self, payment, note, query=""):
        return self.client.post(f"{self.url}{query}", {"reject_form": "", "payment": payment.uuid, "note": note})

    def test_rejecting_keeps_the_guardian_on_free_and_returns_to_the_same_tab(self):
        payment = make_payment(self.nanay)
        self.login_as("developer")

        response = self.reject(payment, "Malabo ang larawan.", query="?status=pending")
        self.assertRedirects(response, f"{self.url}?status=pending")
        self.assertEqual(messages_of(response), ["Tinanggihan ang bayad ni Nanay Rosa."])
        payment.refresh_from_db()
        self.assertEqual((payment.status, payment.note, payment.reviewed_by), (REJECTED, "Malabo ang larawan.", self.developer))
        self.assertEqual(current_plan(self.nanay).key, FREE)

        # Rejecting it again changes nothing.
        self.assertEqual(messages_of(self.reject(payment, "Huli na.")), ["Hindi na naghihintay ang bayad na ito."])

    def test_a_reason_that_is_not_valid_reopens_the_dialog_with_what_was_typed(self):
        payment = make_payment(self.nanay)
        other = make_payment(self.tatay)
        self.login_as("developer")

        too_long = "Malabo ang larawan. " + "a" * 300
        response = self.reject(payment, too_long, query="?status=pending")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["rejecting"], payment.uuid)
        self.assertContains(response, f'data-modal="reject-{payment.uuid}" data-open="true"')
        self.assertContains(response, f'data-modal="reject-{other.uuid}" data-open="false"')
        self.assertContains(response, f">{too_long}</textarea>")
        self.assertContains(response, "Masyadong mahaba ang dahilan (hanggang 300 character).")
        # Still on the tab it was sent from.
        self.assertEqual([tab["label"] for tab in response.context["tabs"] if tab["active"]], ["Naghihintay"])
        self.assertContains(response, f'action="{self.url}?status=pending"')
        payment.refresh_from_db()
        self.assertEqual(payment.status, PENDING)

        response = self.reject(payment, "")
        self.assertContains(response, "Ilagay kung bakit tinanggihan ang bayad.")

    def test_a_payment_not_on_the_page_shows_why_as_a_message(self):
        payment = make_payment(self.nanay)
        self.login_as("developer")
        response = self.reject(payment, "", query="?status=approved")
        self.assertEqual(messages_of(response), ["Ilagay kung bakit tinanggihan ang bayad."])
        self.assertIsNone(response.context["rejecting"])

    def test_only_admins_approve_or_reject(self):
        payment = make_payment(self.nanay)
        approve_url = reverse("approve_payment", args=[payment.uuid])
        self.login_as("nanay")
        self.assertEqual(self.client.post(approve_url).status_code, 302)
        self.assertEqual(self.reject(payment, "x").status_code, 302)
        self.login_as("developer")
        self.assertEqual(self.client.get(approve_url).status_code, 405)
        payment.refresh_from_db()
        self.assertEqual(payment.status, PENDING)

    def test_the_way_back_stays_on_this_page(self):
        payment = make_payment(self.nanay)
        self.login_as("developer")
        response = self.client.post(reverse("approve_payment", args=[payment.uuid]), {"next": "https://iba.example/"})
        self.assertRedirects(response, self.url)
