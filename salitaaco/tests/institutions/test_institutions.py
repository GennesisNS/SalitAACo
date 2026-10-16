from datetime import date

from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.forms.institutions.institution import InstitutionForm
from salitaaco.models.institution import Institution
from salitaaco.tests.users_base import UserBase, make_guardian


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class InstitutionsTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa")
        cls.url = reverse("institutions")

    def data(self, **changes):
        return {"name": "SPED Center ng Barangay", "contact_person": "Gng. Reyes", "contact_details": "0917 000 0000",
                "seats": "20", "plan_notes": "Napagkasunduan kada taon", "renewal_date": "2027-06-01", "is_active": "on",
                **changes}

    def test_form_needs_a_name_and_a_sensible_number(self):
        form = InstitutionForm({})
        self.assertEqual(form.errors["name"], ["Ilagay ang pangalan ng institusyon."])
        self.assertEqual(form.errors["seats"], ["Ilagay kung ilang bata ang sakop."])
        self.assertEqual(InstitutionForm(self.data(seats="-1")).errors["seats"], ["Hindi tama ang bilang."])
        self.assertEqual(InstitutionForm(self.data(renewal_date="bukas")).errors["renewal_date"], ["Hindi tama ang petsa."])
        self.assertTrue(InstitutionForm({"name": "Paaralan", "seats": "0"}).is_valid())

    def test_only_admins_open_the_pages(self):
        institution = Institution.objects.create(name="Paaralan", seats=5)
        urls = [self.url, reverse("edit_institution", args=[institution.uuid])]
        for url in urls:
            self.assertRedirects(self.client.get(url), f"/login/?next={url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 302, f"{username} {url}")
            self.assertEqual(self.client.post(self.url, self.data()).status_code, 302)
            self.assertEqual(self.client.post(reverse("delete_institution", args=[institution.uuid])).status_code, 302)
        self.assertEqual(Institution.objects.count(), 1)

    def test_page_starts_empty_and_is_in_the_sidebar(self):
        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertContains(response, "Wala pang naitalang institusyon.")
        self.assertContains(response, f'<a class="sidebarItem active" href="{self.url}" aria-current="page">')
        # Whether an institution is active is a switch, like every other on/off choice.
        self.assertContains(response, '<label class="switch">', count=1)

    def test_adding_listing_editing_and_deleting(self):
        self.login_as("developer")
        response = self.client.post(self.url, self.data())
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naidagdag na ang SPED Center ng Barangay."])
        institution = Institution.objects.get()
        self.assertEqual((institution.seats, institution.renewal_date, institution.is_active), (20, date(2027, 6, 1), True))

        response = self.client.get(self.url)
        self.assertEqual((response.context["active_count"], response.context["total_count"]), (1, 1))
        self.assertContains(response, "SPED Center ng Barangay")
        self.assertContains(response, "<th>Aksyon</th>")
        edit_url = reverse("edit_institution", args=[institution.uuid])
        self.assertContains(response, f'href="{edit_url}"')

        # Leaving the switch off makes it inactive.
        changed = self.data(seats="35")
        del changed["is_active"]
        self.assertRedirects(self.client.post(edit_url, changed), self.url)
        institution.refresh_from_db()
        self.assertEqual((institution.seats, institution.is_active), (35, False))
        self.assertContains(self.client.get(self.url), '<span class="statusBadge rejected">Hindi aktibo</span>')

        delete_url = reverse("delete_institution", args=[institution.uuid])
        self.assertEqual(self.client.get(delete_url).status_code, 405)
        response = self.client.post(delete_url)
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response)[-1], "Nabura na ang SPED Center ng Barangay.")
        self.assertFalse(Institution.objects.exists())

    def test_a_form_that_is_not_valid_saves_nothing(self):
        self.login_as("developer")
        response = self.client.post(self.url, self.data(name=""))
        self.assertContains(response, "Ilagay ang pangalan ng institusyon.")
        self.assertContains(response, 'data-modal="add-institution" data-open="true"')
        self.assertFalse(Institution.objects.exists())
