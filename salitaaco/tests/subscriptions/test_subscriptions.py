from django.test import SimpleTestCase
from django.urls import reverse

from salitaaco.defaults.plans import APPROVED, FREE, PENDING, PLUS, REJECTED
from salitaaco.forms.subscriptions.reject_payment import RejectPaymentForm
from salitaaco.models.plan import Plan
from salitaaco.tests.payments_base import make_payment, messages_of
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.plans import approve_payment, current_plan


class SubscriptionsPageTest(UserBase):
    url = reverse("subscriptions")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben")

    def test_only_admins_open_the_page(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
        self.login_as("developer")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_the_cards_count_guardians_by_plan_and_this_months_revenue(self):
        approve_payment(make_payment(self.nanay), self.developer)
        make_payment(self.tatay)  # waiting: neither counted nor earned

        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertEqual(
            [(card["label"], card["value"]) for card in response.context["stat_cards"]],
            [("Mga tagapag-alaga", 2), ("Naka-Free", 1), ("Naka-SalitAACo Plus", 1), ("Kita ngayong buwan", "₱149")],
        )

    def test_the_plans_are_set_up_in_system_settings_not_here(self):
        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertNotContains(response, "<h2>Mga plano</h2>")
        self.assertNotContains(response, 'name="plan_form"')
        self.assertContains(response, f'href="{reverse("system_plans")}"')

        # A plan's form sent here changes nothing.
        self.client.post(self.url, {"plan_form": PLUS, "plus-name": "Iba", "plus-price": "1", "plus-features": "x"})
        self.assertEqual(Plan.objects.get(key=PLUS).name, "SalitAACo Plus")

    def test_the_admin_sidebar_lists_both_pages(self):
        self.login_as("developer")
        items = [
            item["id"] for category in self.client.get(self.url).context["navigation_items"] for item in category["items"]
        ]
        # Side by side, under "Negosyo".
        self.assertEqual(items[items.index("revenue"):items.index("revenue") + 2], ["revenue", "subscriptions"])


class RejectPaymentFormTest(SimpleTestCase):
    def test_rejecting_needs_a_payment_and_a_reason(self):
        self.assertEqual(RejectPaymentForm({}).errors["note"], ["Ilagay kung bakit tinanggihan ang bayad."])
        self.assertEqual(
            RejectPaymentForm({"note": "a" * 301}).errors["note"],
            ["Masyadong mahaba ang dahilan (hanggang 300 character)."],
        )
        payment = "6f1c2b8e-3a4d-4c5e-9f00-112233445566"
        self.assertTrue(RejectPaymentForm({"payment": payment, "note": "Malabo ang larawan."}).is_valid())
        self.assertIn("payment", RejectPaymentForm({"payment": "hindi-uuid", "note": "Malabo ang larawan."}).errors)


class PendingPaymentsTest(UserBase):
    """The payments waiting for an admin, approved or rejected on Mga Subscription."""
    url = reverse("subscriptions")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben")

    def reject(self, payment, note, query=""):
        return self.client.post(f"{self.url}{query}", {"reject_form": "", "payment": payment.uuid, "note": note})

    def test_only_the_waiting_payments_are_listed_oldest_first_with_their_buttons(self):
        first = make_payment(self.tatay)
        second = make_payment(self.nanay)
        make_payment(self.nanay, status=APPROVED)
        make_payment(self.nanay, status=REJECTED, note="Mali.")

        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["pending_payments"]), [first, second])
        self.assertEqual(response.context["pending_count"], 2)
        for column in ["Petsa", "Tagapag-alaga", "Plano", "Halaga", "Patunay", "Aksyon"]:
            self.assertContains(response, f"<th>{column}</th>")
        for payment in [first, second]:
            self.assertContains(response, f'data-open-modal="approve-{payment.uuid}">Aprubahan</button>', count=1)
            self.assertContains(response, f'data-open-modal="reject-{payment.uuid}">Tanggihan</button>', count=1)
            self.assertContains(response, f'action="{reverse("approve_payment", args=[payment.uuid])}"', count=1)
            self.assertContains(response, f'<input type="hidden" name="payment" value="{payment.uuid}" />', count=1)
            self.assertContains(response, reverse("view_payment_proof", args=[payment.uuid]))
        self.assertContains(response, 'data-open-modal="proof"', count=2)

    def test_with_none_waiting_it_says_so(self):
        self.login_as("developer")
        self.assertContains(self.client.get(self.url), "Walang bayad na naghihintay.")

    def test_approving_starts_the_plan_and_shows_in_kita_and_the_numbers(self):
        payment = make_payment(self.nanay)
        self.login_as("developer")
        response = self.client.post(reverse("approve_payment", args=[payment.uuid]), {"next": "?pending_page=1"})

        self.assertRedirects(response, f"{self.url}?pending_page=1")
        self.assertEqual(messages_of(response), ["Naaprubahan na. Naka-SalitAACo Plus na si Nanay Rosa."])
        payment.refresh_from_db()
        self.assertEqual((payment.status, payment.reviewed_by), (APPROVED, self.developer))
        self.assertEqual(current_plan(self.nanay).key, PLUS)

        response = self.client.get(self.url)
        self.assertEqual(list(response.context["pending_payments"]), [])
        cards = {card["label"]: card["value"] for card in response.context["stat_cards"]}
        self.assertEqual((cards["Naka-SalitAACo Plus"], cards["Kita ngayong buwan"]), (1, "₱149"))
        kita = self.client.get(reverse("revenue"), {"status": "approved"})
        self.assertEqual(list(kita.context["payments"]), [payment])

        # Approving it again changes nothing.
        response = self.client.post(reverse("approve_payment", args=[payment.uuid]))
        self.assertEqual(messages_of(response), ["Hindi na naghihintay ang bayad na ito."])

    def test_the_way_back_stays_on_this_page(self):
        payment = make_payment(self.nanay)
        self.login_as("developer")
        response = self.client.post(reverse("approve_payment", args=[payment.uuid]), {"next": "https://iba.example/"})
        self.assertRedirects(response, self.url)

    def test_rejecting_keeps_the_guardian_on_free_and_shows_in_kita(self):
        payment = make_payment(self.nanay)
        self.login_as("developer")

        response = self.reject(payment, "Malabo ang larawan.", query="?pending_page=1")
        self.assertRedirects(response, f"{self.url}?pending_page=1")
        self.assertEqual(messages_of(response), ["Tinanggihan ang bayad ni Nanay Rosa."])
        payment.refresh_from_db()
        self.assertEqual((payment.status, payment.note, payment.reviewed_by), (REJECTED, "Malabo ang larawan.", self.developer))
        self.assertEqual(current_plan(self.nanay).key, FREE)
        kita = self.client.get(reverse("revenue"), {"status": "rejected"})
        self.assertEqual(list(kita.context["payments"]), [payment])

        # Rejecting it again changes nothing.
        self.assertEqual(messages_of(self.reject(payment, "Huli na.")), ["Hindi na naghihintay ang bayad na ito."])

    def test_a_reason_that_is_not_valid_reopens_the_dialog_with_what_was_typed(self):
        payment = make_payment(self.nanay)
        other = make_payment(self.tatay)
        self.login_as("developer")

        too_long = "Malabo ang larawan. " + "a" * 300
        response = self.reject(payment, too_long)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["rejecting"], payment.uuid)
        self.assertContains(response, f'data-modal="reject-{payment.uuid}" data-open="true"')
        self.assertContains(response, f'data-modal="reject-{other.uuid}" data-open="false"')
        self.assertContains(response, f">{too_long}</textarea>")
        self.assertContains(response, "Masyadong mahaba ang dahilan (hanggang 300 character).")
        payment.refresh_from_db()
        self.assertEqual(payment.status, PENDING)

        self.assertContains(self.reject(payment, ""), "Ilagay kung bakit tinanggihan ang bayad.")

    def test_a_payment_not_in_the_list_shows_why_as_a_message(self):
        # No longer waiting, so it has no dialog to reopen.
        payment = make_payment(self.nanay, status=APPROVED)
        self.login_as("developer")
        response = self.reject(payment, "")
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
