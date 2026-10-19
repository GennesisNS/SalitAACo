from django.test import SimpleTestCase
from django.urls import reverse

from salitaaco.defaults.plans import FREE, PLUS
from salitaaco.forms.subscriptions.plan import MAX_FEATURES, PlanForm
from salitaaco.models.plan import Plan
from salitaaco.tests.payments_base import make_payment, messages_of
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.plans import approve_payment


class PlanFormTest(SimpleTestCase):
    def test_features_are_one_per_line_without_blank_lines(self):
        form = PlanForm({"name": "Plus", "price": "199", "features": "  Isa \n\n Dalawa \n"})
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
        form = PlanForm({"name": "Libre", "features": "Isa"}, include_price=False)
        self.assertTrue(form.is_valid())
        self.assertEqual(set(form.fields), {"name", "features"})


class SubscriptionsPageTest(UserBase):
    url = reverse("subscriptions")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben")

    def edit(self, plan_key, **data):
        return self.client.post(self.url, {"plan_form": plan_key, **{f"{plan_key}-{name}": value for name, value in data.items()}})

    def test_only_admins_open_and_save(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.edit(PLUS, name="Na-hack", price="1", features="x")
        self.assertEqual(Plan.objects.get(key=PLUS).name, "SalitAACo Plus")
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
        self.assertEqual([(item["plan"].key, item["subscribers"]) for item in response.context["plans"]],
                         [(FREE, 1), (PLUS, 1)])

    def test_each_plan_is_a_form_and_free_has_no_price(self):
        self.login_as("developer")
        response = self.client.get(self.url)

        self.assertContains(response, 'name="plus-name" value="SalitAACo Plus"')
        self.assertContains(response, 'name="plus-price" value="149"')
        self.assertNotContains(response, 'name="free-price"')
        self.assertContains(response, "Boses ng pamilya (family voice banking)\nMada-download na ulat ng paggamit")
        # Whether Plus is offered is a switch; Free is always offered.
        self.assertContains(response, '<label class="switch">', count=1)
        self.assertContains(response, 'name="plus-offered"')
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

    def test_the_admin_sidebar_lists_both_pages(self):
        self.login_as("developer")
        items = [
            item["id"] for category in self.client.get(self.url).context["navigation_items"] for item in category["items"]
        ]
        # Side by side, under "Negosyo".
        self.assertEqual(items[items.index("revenue"):items.index("revenue") + 2], ["revenue", "subscriptions"])
