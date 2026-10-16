from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.forms.support.contact_support import ContactSupportForm
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.support_message import SupportMessage
from salitaaco.tests.users_base import UserBase, make_guardian


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class SupportBase(UserBase):
    """Nanay is Miguel's guardian. Tatay is Ana's."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben", children=[cls.ana])
        cls.miguel_account = ChildAccount.objects.get(user=cls.miguel)
        cls.ana_account = ChildAccount.objects.get(user=cls.ana)
        cls.url = reverse("support")


class ContactSupportFormTest(SupportBase):
    def test_a_message_is_required_and_the_child_is_not(self):
        form = ContactSupportForm({"child": "", "message": "  "}, children=[self.miguel_account])
        self.assertEqual(form.errors["message"], ["Ilarawan ang problema o tanong."])

        form = ContactSupportForm({"child": "", "message": "Walang tunog."}, children=[self.miguel_account])
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.chosen_child())

    def test_only_the_guardians_own_children_can_be_named(self):
        form = ContactSupportForm({"child": str(self.miguel_account.uuid), "message": "Walang tunog."}, children=[self.miguel_account])
        self.assertTrue(form.is_valid())
        self.assertEqual(form.chosen_child(), self.miguel_account)

        form = ContactSupportForm({"child": str(self.ana_account.uuid), "message": "Walang tunog."}, children=[self.miguel_account])
        self.assertEqual(form.errors["child"], ["Pumili ng bata mula sa listahan."])

    def test_a_message_has_a_limit(self):
        form = ContactSupportForm({"message": "a" * 2001})
        self.assertEqual(form.errors["message"], ["Masyadong mahaba ang mensahe (hanggang 2000 character)."])


class SupportPageTest(SupportBase):
    def test_only_guardians_open_the_page(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "developer"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)

        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<details class="guide">', count=5)
        self.assertContains(response, "Makipag-ugnayan sa suporta")
        # Only her own child is offered.
        self.assertContains(response, "Miguel</option>")
        self.assertNotContains(response, "Ana</option>")

    def test_sending_a_message_saves_it_and_shows_it_back(self):
        self.login_as("nanay")
        text = "Hindi lumalabas ang larawan ni Lola sa tile."
        response = self.client.post(self.url, {"child": str(self.miguel_account.uuid), "message": text})

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naipadala na ang mensahe mo. Salamat!"])
        sent = SupportMessage.objects.get()
        self.assertEqual((sent.guardian, sent.child, sent.message), (self.nanay, self.miguel_account, text))

        response = self.client.get(self.url)
        self.assertContains(response, text)
        self.assertContains(response, "tungkol kay Miguel")

        # Another guardian does not see it.
        self.login_as("tatay")
        self.assertNotContains(self.client.get(self.url), text)

    def test_a_message_that_is_not_valid_is_not_saved(self):
        self.login_as("nanay")
        response = self.client.post(self.url, {"child": str(self.ana_account.uuid), "message": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ilarawan ang problema o tanong.")
        self.assertContains(response, "Pumili ng bata mula sa listahan.")
        self.assertFalse(SupportMessage.objects.exists())

    def test_a_message_outlives_the_child_but_not_the_guardian(self):
        SupportMessage.objects.create(guardian=self.nanay, child=self.miguel_account, message="Tulong po.")
        self.miguel.delete()
        self.assertIsNone(SupportMessage.objects.get().child)

        self.nanay.user.delete()
        self.assertFalse(SupportMessage.objects.exists())
