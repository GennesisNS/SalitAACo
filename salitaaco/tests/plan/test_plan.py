from datetime import datetime, timedelta

from django.core.files.storage import default_storage
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from salitaaco.defaults.plans import APPROVED, FREE, PENDING, PLUS, REJECTED
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan
from salitaaco.tests.payments_base import make_payment, messages_of, set_gcash_qr
from salitaaco.tests.users_base import UserBase, image_upload, make_guardian
from salitaaco.utils.account import delete_user_account
from salitaaco.utils.plans import (
    add_months,
    approve_payment,
    current_plan,
    paid_until,
    reject_payment,
    revenue_this_month,
    subscriber_counts,
)


class PlanModelTest(TestCase):
    def test_the_migration_made_the_two_starting_plans(self):
        self.assertEqual(
            [(plan.key, plan.name, plan.price, plan.offered, plan.period) for plan in Plan.objects.all()],
            [(FREE, "Free", 0, True, "habambuhay"), (PLUS, "SalitAACo Plus", 149, True, "kada buwan")],
        )
        plus = Plan.objects.get(key=PLUS)
        self.assertEqual(plus.feature_list[1], "Boses ng pamilya (family voice banking)")
        self.assertTrue(Plan.objects.get(key=FREE).is_default)

    def test_a_month_later_is_the_same_day_or_the_last_of_a_shorter_month(self):
        def at(year, month, day):
            return timezone.make_aware(datetime(year, month, day, 9, 30))

        self.assertEqual(add_months(at(2026, 10, 19), 1), at(2026, 11, 19))
        self.assertEqual(add_months(at(2026, 12, 5), 1), at(2027, 1, 5))
        self.assertEqual(add_months(at(2027, 1, 31), 1), at(2027, 2, 28))
        self.assertEqual(add_months(at(2028, 1, 31), 1), at(2028, 2, 29))


class PlanBase(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben")


class ApprovingTest(PlanBase):
    def test_a_guardian_without_an_approved_payment_is_on_free(self):
        make_payment(self.nanay)  # waiting
        make_payment(self.nanay, status=REJECTED)
        self.assertEqual(current_plan(self.nanay).key, FREE)
        self.assertIsNone(paid_until(self.nanay))

    def test_approving_gives_a_month_of_the_plan(self):
        payment = make_payment(self.nanay)
        before = timezone.now()
        self.assertTrue(approve_payment(payment, self.developer))

        payment.refresh_from_db()
        self.assertEqual(payment.status, APPROVED)
        self.assertEqual(payment.reviewed_by, self.developer)
        self.assertGreaterEqual(payment.starts_at, before)
        self.assertEqual(payment.ends_at, add_months(payment.starts_at, 1))
        self.assertEqual(current_plan(self.nanay).key, PLUS)
        self.assertEqual(paid_until(self.nanay), payment.ends_at)
        # Only her plan changed.
        self.assertEqual(current_plan(self.tatay).key, FREE)

    def test_paying_again_before_the_month_ends_adds_to_the_end(self):
        first = make_payment(self.nanay)
        approve_payment(first, self.developer)
        first.refresh_from_db()

        second = make_payment(self.nanay)
        approve_payment(second, self.developer)
        second.refresh_from_db()

        self.assertEqual(second.starts_at, first.ends_at)
        self.assertEqual(second.ends_at, add_months(first.ends_at, 1))
        self.assertEqual(paid_until(self.nanay), second.ends_at)
        self.assertEqual(current_plan(self.nanay).key, PLUS)

    def test_after_the_month_the_guardian_is_back_on_free(self):
        payment = make_payment(self.nanay)
        approve_payment(payment, self.developer)
        Payment.objects.filter(pk=payment.pk).update(
            starts_at=timezone.now() - timedelta(days=40), ends_at=timezone.now() - timedelta(days=10),
        )
        self.assertEqual(current_plan(self.nanay).key, FREE)
        self.assertIsNone(paid_until(self.nanay))

        # A payment after it ended starts now, not where the old one ended.
        again = make_payment(self.nanay)
        approve_payment(again, self.developer)
        again.refresh_from_db()
        self.assertGreater(again.starts_at, timezone.now() - timedelta(minutes=1))

    def test_rejecting_keeps_the_plan_and_says_why(self):
        payment = make_payment(self.nanay)
        self.assertTrue(reject_payment(payment, self.developer, "Malabo ang larawan."))
        payment.refresh_from_db()
        self.assertEqual((payment.status, payment.note, payment.starts_at), (REJECTED, "Malabo ang larawan.", None))
        self.assertEqual(current_plan(self.nanay).key, FREE)

    def test_a_payment_is_decided_once(self):
        payment = make_payment(self.nanay)
        approve_payment(payment, self.developer)
        self.assertFalse(approve_payment(payment, self.developer))
        self.assertFalse(reject_payment(payment, self.developer, "Huli na"))
        payment.refresh_from_db()
        self.assertEqual((payment.status, payment.note), (APPROVED, ""))

    def test_counts_and_revenue(self):
        approve_payment(make_payment(self.nanay), self.developer)
        reject_payment(make_payment(self.tatay), self.developer, "Mali ang halaga.")
        make_payment(self.tatay)

        self.assertEqual(subscriber_counts(), {PLUS: 1, FREE: 1})
        self.assertEqual(revenue_this_month(), 149)


class PlanPageTest(PlanBase):
    url = reverse("plan")

    def send_proof(self, **data):
        return self.client.post(self.url, {"proof_form": "", "plan": PLUS, "proof": image_upload(), **data})

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
        response = self.client.get(self.url)

        self.assertEqual(response.context["current_plan"].key, FREE)
        self.assertEqual(
            [(item["plan"].key, item["is_current"], item["needs_payment"]) for item in response.context["plans"]],
            [(FREE, True, False), (PLUS, False, True)],
        )
        self.assertContains(response, "₱0")
        self.assertContains(response, "₱149")
        self.assertContains(response, "Kunin ang SalitAACo Plus")
        self.assertContains(response, f'href="{reverse("plan_transactions")}"')

    def test_without_a_qr_code_nobody_can_pay(self):
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, "Wala pang QR code")
        self.assertContains(response, 'name="proof_form" disabled')

        response = self.send_proof()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wala pang QR code ng GCash. Hindi pa makakabayad.")
        self.assertFalse(Payment.objects.exists())

    def test_the_pay_window_shows_the_qr_code_and_the_gcash_account(self):
        setting = set_gcash_qr()
        setting.gcash_name = "Juan D."
        setting.gcash_number = "0917 000 0000"
        setting.save()

        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, f'<img src="{reverse("view_gcash_qr")}?v=')
        self.assertContains(response, "<b>Juan D.</b>")
        self.assertContains(response, "GCash 0917 000 0000")
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertNotContains(response, 'name="proof_form" disabled')

    def test_sending_a_proof_makes_a_waiting_payment(self):
        set_gcash_qr()
        self.login_as("nanay")
        response = self.send_proof()

        self.assertRedirects(response, reverse("plan_transactions"))
        self.assertEqual(messages_of(response), ["Naipadala na ang patunay ng bayad. Hintayin ang pag-apruba ng admin."])
        payment = Payment.objects.get()
        self.assertEqual((payment.guardian, payment.plan.key, payment.amount, payment.status), (self.nanay, PLUS, 149, PENDING))
        # The stored name is random, never the one the browser sent.
        self.assertTrue(payment.proof.name.startswith("payment-proofs/"))
        self.assertNotIn("larawan", payment.proof.name)
        # Her plan does not change until an admin approves.
        self.assertEqual(current_plan(self.nanay).key, FREE)

        response = self.client.get(self.url)
        self.assertContains(response, "May bayad kang naghihintay ng pag-apruba ng admin")
        self.assertContains(response, 'data-open-modal="pay" disabled')

    def test_one_payment_waits_at_a_time(self):
        set_gcash_qr()
        make_payment(self.nanay)
        self.login_as("nanay")
        self.assertContains(self.send_proof(), "May bayad ka pang naghihintay ng admin.")
        self.assertEqual(Payment.objects.count(), 1)

    def test_a_proof_that_is_not_a_picture_is_refused_and_the_window_reopens(self):
        set_gcash_qr()
        self.login_as("nanay")
        for proof, error in [
            (image_upload("bayad.gif", "GIF", "image/gif"), "JPEG, PNG o WebP lang ang puwedeng larawan."),
            (image_upload(padding=5 * 1024 * 1024), "Masyadong malaki ang larawan (max 5MB)."),
        ]:
            response = self.send_proof(proof=proof)
            self.assertContains(response, error)
            self.assertContains(response, 'data-modal="pay" data-open="true"')
        response = self.client.post(self.url, {"proof_form": "", "plan": PLUS})
        self.assertContains(response, "Pumili ng larawan ng matagumpay na bayad.")
        self.assertFalse(Payment.objects.exists())

    def test_a_plan_that_is_not_offered_cannot_be_paid_for(self):
        set_gcash_qr()
        self.login_as("nanay")
        # Nor can the free one.
        self.assertContains(self.send_proof(plan=FREE), "Hindi na iniaalok ang planong ito.")

        Plan.objects.filter(key=PLUS).update(offered=False)
        self.assertNotContains(self.client.get(self.url), 'data-modal="pay"')
        self.assertEqual(self.send_proof().status_code, 200)
        self.assertFalse(Payment.objects.exists())

    def test_on_plus_the_page_says_until_when_and_offers_another_month(self):
        approve_payment(make_payment(self.nanay), self.developer)
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertEqual(response.context["current_plan"].key, PLUS)
        self.assertContains(response, "Kasalukuyang plano: <b>SalitAACo Plus</b>, hanggang")
        self.assertContains(response, "Dagdagan ng isang buwan")

    def test_the_sidebar_and_the_overview_lead_to_the_plan(self):
        self.login_as("nanay")
        response = self.client.get(reverse("overview"))
        self.assertContains(response, f'href="{self.url}"', count=2)
        self.assertContains(response, "Kasalukuyang plano: <b>Free</b>")

        items = {
            item["id"]: item for category in self.client.get(reverse("plan_transactions")).context["navigation_items"]
            for item in category["items"]
        }
        self.assertTrue(items["plan"]["active"])


class TransactionHistoryTest(PlanBase):
    url = reverse("plan_transactions")

    def test_history_is_empty_before_the_first_payment(self):
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, "Wala ka pang bayad.")
        self.assertNotContains(response, "<table>")

    def test_history_lists_only_her_payments_with_what_became_of_them(self):
        approve_payment(make_payment(self.nanay), self.developer)
        reject_payment(make_payment(self.nanay), self.developer, "Malabo ang larawan ng bayad.")
        make_payment(self.nanay)
        make_payment(self.tatay)

        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertEqual(
            [payment.status for payment in response.context["payments"]], [PENDING, REJECTED, APPROVED],
        )
        for status in [PENDING, APPROVED, REJECTED]:
            self.assertContains(response, f'<span class="statusBadge {status}">')
        self.assertContains(response, "Malabo ang larawan ng bayad.")
        self.assertContains(response, " hanggang ", count=1)
        self.assertContains(response, 'data-proof-url="', count=3)


class PrivateFilesTest(PlanBase):
    def test_only_the_guardian_who_sent_it_and_admins_open_a_proof(self):
        payment = make_payment(self.nanay)
        url = reverse("view_payment_proof", args=[payment.uuid])

        self.assertRedirects(self.client.get(url), f"/login/?next={url}")
        self.login_as("miguel")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.login_as("tatay")
        self.assertEqual(self.client.get(url).status_code, 404)
        for username in ["nanay", "developer"]:
            self.login_as(username)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, username)
            self.assertEqual(response["Content-Type"], "image/png")
            self.assertEqual(response["Cache-Control"], "private, max-age=86400")

    def test_the_qr_code_is_for_guardians_and_admins(self):
        url = reverse("view_gcash_qr")
        self.login_as("nanay")
        self.assertEqual(self.client.get(url).status_code, 404)

        set_gcash_qr()
        for username in ["nanay", "developer"]:
            self.login_as(username)
            self.assertEqual(self.client.get(url).status_code, 200, username)
        self.login_as("miguel")
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_deleting_the_guardian_deletes_the_proofs(self):
        payment = make_payment(self.tatay)
        name = payment.proof.name
        self.assertTrue(default_storage.exists(name))

        delete_user_account(self.tatay.user)
        self.assertFalse(Payment.objects.exists())
        self.assertFalse(default_storage.exists(name))
