from django.test import SimpleTestCase
from django.urls import reverse

from salitaaco.defaults.plans import FREE, PLUS
from salitaaco.forms.subscriptions.plan import MAX_FEATURES, PlanForm
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan
from salitaaco.tests.payments_base import make_payment, messages_of, set_gcash_qr
from salitaaco.tests.users_base import UserBase, image_upload, make_guardian
from salitaaco.utils.plans import approve_payment

# The key a plan named "SalitAACo Pamilya" gets: its name as a slug, cut short.
PAMILYA = "salitaaco-pami"


class PlanFormTest(SimpleTestCase):
    def test_features_are_one_per_line_without_blank_lines(self):
        form = PlanForm({"name": "Plus", "price": "199", "features": "  Isa \n\n Dalawa \n", "child_limit": "3"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["features"], "Isa\nDalawa")

        self.assertEqual(PlanForm({"name": "Plus", "price": "199", "features": " \n "}).errors["features"],
                         ["Ilagay kahit isang kasama sa plano."])
        too_many = "\n".join(f"Kasama {number}" for number in range(MAX_FEATURES + 1))
        self.assertIn("features", PlanForm({"name": "Plus", "price": "199", "features": too_many}).errors)

    def test_a_paid_plan_costs_at_least_a_peso(self):
        self.assertEqual(PlanForm({"name": "Plus", "price": "0", "features": "Isa"}).errors["price"],
                         ["Hindi bababa sa ₱1 ang presyo ng bayad na plano."])

    def test_the_default_plan_has_no_price_or_offered_switch(self):
        form = PlanForm({"name": "Libre", "features": "Isa", "child_limit": "1"}, include_price=False)
        self.assertTrue(form.is_valid())
        self.assertEqual(set(form.fields), {"name", "features", "child_limit"})


class PlansBase(UserBase):
    url = reverse("system_plans")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])

    def edit(self, plan_key, **data):
        # A plan's child limit is left as it is unless a test changes it.
        data = {"child_limit": str(Plan.objects.get(key=plan_key).child_limit), **data}
        return self.client.post(self.url, {"plan_form": plan_key, **{f"{plan_key}-{name}": value for name, value in data.items()}})

    def add(self, **data):
        fields = {
            "name": "SalitAACo Pamilya", "price": "299", "features": "Lahat ng nasa Plus\nHanggang 5 bata",
            "child_limit": "5", "offered": "on", **data,
        }
        return self.client.post(self.url, {"new_plan_form": "", **{f"new-{name}": value for name, value in fields.items()}})


class PlansPageTest(PlansBase):
    def test_only_admins_open_and_change_the_plans(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.edit(PLUS, name="Na-hack", price="1", features="x")
            self.add()
        self.assertEqual(Plan.objects.get(key=PLUS).name, "SalitAACo Plus")
        self.assertEqual(Plan.objects.count(), 2)

        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # It is a page of System Settings, beside General.
        self.assertContains(response, f'<a class="sidebarItem active" href="{self.url}" aria-current="page">')
        items = [item["id"] for category in response.context["navigation_items"] for item in category["items"]]
        self.assertEqual(items[items.index("system_general"):items.index("system_general") + 2], ["system_general", "system_plans"])

    def test_each_plan_is_a_form_and_free_has_no_price(self):
        self.login_as("developer")
        response = self.client.get(self.url)

        self.assertContains(response, 'name="plus-name" value="SalitAACo Plus"')
        self.assertContains(response, 'name="plus-price" value="149"')
        self.assertNotContains(response, 'name="free-price"')
        self.assertContains(response, "Boses ng pamilya (family voice banking)\nMada-download na ulat ng paggamit")
        self.assertContains(response, 'name="plus-offered"')
        self.assertNotContains(response, 'name="free-offered"')
        self.assertContains(response, 'name="plan_form" value="free"')
        self.assertContains(response, 'name="plan_form" value="plus"')

    def test_editing_plus_shows_everywhere_and_leaves_sent_payments_alone(self):
        payment = make_payment(self.nanay)

        self.login_as("developer")
        response = self.edit(PLUS, name="SalitAACo Pamilya", price="199", features="Lahat ng nasa Free\nBagong kasama", offered="on")
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naka-save na ang SalitAACo Pamilya."])

        plus = Plan.objects.get(key=PLUS)
        self.assertEqual((plus.name, plus.price, plus.feature_list, plus.offered),
                         ("SalitAACo Pamilya", 199, ["Lahat ng nasa Free", "Bagong kasama"], True))
        payment.refresh_from_db()
        self.assertEqual(payment.amount, 149)

        self.client.post(reverse("logout"))
        public = self.client.get("/")
        self.assertContains(public, "SalitAACo Pamilya")
        self.assertContains(public, "₱199")
        self.assertContains(public, "Bagong kasama")

    def test_a_plan_taken_off_offer_disappears_for_guardians(self):
        self.login_as("developer")
        self.edit(PLUS, name="SalitAACo Plus", price="149", features="Isa")  # the switch left off
        self.assertFalse(Plan.objects.get(key=PLUS).offered)

        self.login_as("nanay")
        self.assertNotContains(self.client.get(reverse("plan")), "<h2>SalitAACo Plus</h2>")

    def test_a_guardian_keeps_seeing_the_plan_they_are_on_after_it_is_taken_off_offer(self):
        approve_payment(make_payment(self.nanay), self.developer)
        Plan.objects.filter(key=PLUS).update(offered=False)

        self.login_as("nanay")
        response = self.client.get(reverse("plan"))
        self.assertEqual([(item["plan"].key, item["is_current"], item["needs_payment"]) for item in response.context["plans"]],
                         [(FREE, False, False), (PLUS, True, False)])
        self.assertContains(response, "Ito ang plano mo")
        # It cannot be paid for again, nor chosen by anyone else.
        self.assertNotContains(response, f'data-pay-plan="{PLUS}"')
        self.client.post(reverse("logout"))
        self.assertNotContains(self.client.get("/"), "SalitAACo Plus")

    def test_no_two_plans_have_the_same_name(self):
        self.login_as("developer")
        response = self.edit(PLUS, name="free", price="149", features="Isa", offered="on")
        self.assertContains(response, "May plano nang may ganitong pangalan.")
        self.assertEqual(Plan.objects.get(key=PLUS).name, "SalitAACo Plus")

        response = self.add(name="SalitAACo  plus")
        self.assertContains(response, "May plano nang may ganitong pangalan.")
        self.assertEqual(Plan.objects.count(), 2)

        # Saving a plan under its own name is fine.
        self.assertRedirects(self.edit(PLUS, name="SalitAACo Plus", price="149", features="Isa", offered="on"), self.url)

    def test_free_keeps_its_price_and_stays_offered(self):
        self.login_as("developer")
        self.edit(FREE, name="Libre", price="500", features="Isa", offered="")
        free = Plan.objects.get(key=FREE)
        self.assertEqual((free.name, free.price, free.offered), ("Libre", 0, True))

    def test_a_form_that_is_not_valid_saves_nothing_and_shows_why(self):
        self.login_as("developer")
        response = self.edit(PLUS, name="", price="abc", features="Isa", offered="on")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ilagay ang pangalan ng plano.")
        self.assertContains(response, "Hindi tama ang presyo.")
        self.assertEqual(Plan.objects.get(key=PLUS).name, "SalitAACo Plus")

    def test_each_plan_says_how_many_child_accounts_it_allows(self):
        self.assertEqual([(plan.key, plan.child_limit) for plan in Plan.objects.all()], [(FREE, 1), (PLUS, 3)])
        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertContains(response, 'name="free-child_limit" value="1"')
        self.assertContains(response, 'name="plus-child_limit" value="3"')
        self.assertContains(response, 'name="new-child_limit" value="3"')

        self.assertRedirects(self.edit(FREE, name="Free", features="Isa", child_limit="2"), self.url)
        self.assertRedirects(self.edit(PLUS, name="SalitAACo Plus", price="149", features="Isa", child_limit="10", offered="on"), self.url)
        self.assertEqual([plan.child_limit for plan in Plan.objects.all()], [2, 10])

        for value, error in [("0", "Kahit isang account ng bata."), ("51", "Hanggang 50 lang."), ("", "Ilagay ang bilang.")]:
            response = self.edit(PLUS, name="SalitAACo Plus", price="149", features="Isa", child_limit=value, offered="on")
            self.assertContains(response, error)
        self.assertEqual(Plan.objects.get(key=PLUS).child_limit, 10)


class AddPlanTest(PlansBase):
    def test_a_new_plan_comes_last_and_is_offered_to_guardians(self):
        self.login_as("developer")
        response = self.add()
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naidagdag na ang SalitAACo Pamilya."])

        plan = Plan.objects.last()
        self.assertEqual(
            (plan.key, plan.name, plan.price, plan.feature_list, plan.child_limit, plan.offered),
            (PAMILYA, "SalitAACo Pamilya", 299, ["Lahat ng nasa Plus", "Hanggang 5 bata"], 5, True),
        )
        self.assertEqual([plan.key for plan in Plan.objects.all()], [FREE, PLUS, PAMILYA])
        self.assertContains(self.client.get(self.url), f'name="{PAMILYA}-name" value="SalitAACo Pamilya"')

        self.client.post(reverse("logout"))
        self.assertContains(self.client.get("/"), "₱299")

    def test_keys_never_repeat(self):
        # Three names whose key would be "plus", and one whose key would be the new plan form's prefix.
        self.login_as("developer")
        self.add(name="Plus")
        self.add(name="Plus!")
        self.add(name="New")
        self.assertEqual([plan.key for plan in Plan.objects.all()], [FREE, PLUS, "plus-2", "plus-3", "new-2"])

    def test_a_new_plan_that_is_not_valid_reopens_its_window(self):
        self.login_as("developer")
        response = self.add(price="0")
        self.assertContains(response, "Hindi bababa sa ₱1 ang presyo ng bayad na plano.")
        self.assertContains(response, 'data-modal="new-plan" data-open="true"')
        self.assertEqual(Plan.objects.count(), 2)

    def test_a_guardian_pays_for_the_plan_they_pick(self):
        self.login_as("developer")
        self.add()
        set_gcash_qr()

        self.login_as("nanay")
        page = self.client.get(reverse("plan"))
        for key, price in [(PLUS, 149), (PAMILYA, 299)]:
            self.assertContains(page, f'data-pay-plan="{key}"')
            self.assertContains(page, f'data-pay-price="{price}"')
        self.assertContains(page, 'data-modal="pay"', count=1)

        response = self.client.post(reverse("plan"), {"proof_form": "", "plan": PAMILYA, "proof": image_upload()})
        self.assertRedirects(response, reverse("plan_transactions"))
        payment = Payment.objects.get()
        self.assertEqual((payment.plan.key, payment.amount), (PAMILYA, 299))

    def test_a_refused_upload_reopens_the_window_on_the_plan_it_was_for(self):
        self.login_as("developer")
        self.add()
        set_gcash_qr()

        self.login_as("nanay")
        response = self.client.post(reverse("plan"), {"proof_form": "", "plan": PAMILYA})
        self.assertEqual(response.context["pay_plan"].key, PAMILYA)
        self.assertContains(response, f'<input type="hidden" name="plan" value="{PAMILYA}" id="payPlan" />')


class DeletePlanTest(PlansBase):
    def test_a_plan_without_payments_is_deleted(self):
        self.login_as("developer")
        self.add()
        plan = Plan.objects.get(key=PAMILYA)
        url = reverse("remove_plan", args=[plan.plan_id])
        self.assertContains(self.client.get(self.url), f'action="{url}"')
        self.assertEqual(self.client.get(url).status_code, 405)

        response = self.client.post(url)
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Nabura na ang SalitAACo Pamilya."])
        self.assertFalse(Plan.objects.filter(key=PAMILYA).exists())

    def test_free_and_a_plan_with_payments_stay(self):
        make_payment(self.nanay)  # a payment for Plus
        self.login_as("developer")
        page = self.client.get(self.url)
        for key in [FREE, PLUS]:
            plan = Plan.objects.get(key=key)
            self.assertNotContains(page, f'data-modal="delete-plan-{plan.plan_id}"')

        response = self.client.post(reverse("remove_plan", args=[Plan.objects.get(key=FREE).plan_id]))
        self.assertEqual(messages_of(response), ["Hindi mabubura ang libreng plano: dito napupunta ang mga walang bayad na plano."])
        response = self.client.post(reverse("remove_plan", args=[Plan.objects.get(key=PLUS).plan_id]))
        self.assertEqual(
            messages_of(response)[-1],
            "May mga bayad na para sa SalitAACo Plus, kaya hindi ito mabubura. I-off na lang ang “Iniaalok”.",
        )
        self.assertEqual(Plan.objects.count(), 2)

    def test_only_admins_delete(self):
        self.login_as("developer")
        self.add()
        plan = Plan.objects.get(key=PAMILYA)
        self.login_as("nanay")
        self.assertEqual(self.client.post(reverse("remove_plan", args=[plan.plan_id])).status_code, 302)
        self.assertTrue(Plan.objects.filter(pk=plan.pk).exists())
