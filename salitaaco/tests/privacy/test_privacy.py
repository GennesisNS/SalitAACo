from datetime import timedelta

from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from salitaaco.defaults.family_voice import TERMS_VERSION
from salitaaco.forms.privacy.purge_usage import PurgeUsageForm
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.users_base import UserBase, make_guardian


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class PrivacyPageTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.url = reverse("system_privacy")
        cls.today = timezone.localdate()

    def used(self, days_ago, count=1):
        return DailyUsage.objects.create(
            user=self.miguel, kind=DailyUsage.WORD, name=f"salita-{days_ago}", use_count=count,
            day=self.today - timedelta(days=days_ago),
        )

    def test_only_admins_open_the_page_and_delete_counts(self):
        self.used(400)
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.assertEqual(self.client.post(self.url, {"older_than": "90"}).status_code, 302)
        self.assertEqual(DailyUsage.objects.count(), 1)

    def test_page_says_what_is_kept_and_under_which_consent(self):
        self.used(5)
        for version in [TERMS_VERSION, TERMS_VERSION, "2025-01-01"]:
            FamilyVoice.objects.create(guardian=self.nanay, name="Lola", elevenlabs_voice_id="boses",
                                       consent_at=timezone.now(), consent_version=version)
        self.login_as("developer")

        response = self.client.get(self.url)

        kept = {row["what"]: row["count"] for row in response.context["kept"]}
        self.assertEqual(kept["Mga account"], 4)
        self.assertEqual(kept["Mga boses ng pamilya"], 3)
        self.assertEqual(kept["Mga bilang ng paggamit kada araw"], 1)
        self.assertEqual(
            [(row["consent_version"], row["count"]) for row in response.context["consents"]],
            [(TERMS_VERSION, 2), ("2025-01-01", 1)],
        )
        self.assertEqual(response.context["oldest_usage_day"], self.today - timedelta(days=5))
        self.assertContains(response, f"<b>{TERMS_VERSION}</b>")
        self.assertContains(response, "Hindi itinatago ang mga pangungusap na binuo sa board")

    def test_form_takes_only_the_ages_offered(self):
        self.assertEqual(PurgeUsageForm({}).errors["older_than"], ["Pumili kung gaano kaluma."])
        self.assertEqual(PurgeUsageForm({"older_than": "1"}).errors["older_than"], ["Pumili mula sa listahan."])
        form = PurgeUsageForm({"older_than": "180"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.days(), 180)

    def test_deleting_old_counts_keeps_the_newer_ones_and_the_totals(self):
        WordUsage.objects.create(user=self.miguel, word="kain", use_count=50)
        for days_ago in [0, 89, 90, 91, 400]:
            self.used(days_ago)
        self.login_as("developer")

        response = self.client.post(self.url, {"older_than": "90"})

        self.assertRedirects(response, self.url)
        cutoff = self.today - timedelta(days=90)
        self.assertEqual(messages_of(response), [f"Nabura na ang 2 bilang kada araw na mas luma sa {cutoff.isoformat()}."])
        self.assertEqual(sorted((self.today - usage.day).days for usage in DailyUsage.objects.all()), [0, 89, 90])
        # A word's total, which the Paborito screen is drawn from, is not touched.
        self.assertEqual(WordUsage.objects.get().use_count, 50)

    def test_a_choice_that_is_not_offered_deletes_nothing(self):
        self.used(400)
        self.login_as("developer")
        response = self.client.post(self.url, {"older_than": "0"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-modal="purge-usage" data-open="true"')
        self.assertEqual(DailyUsage.objects.count(), 1)
