from unittest import mock

from django.urls import reverse

from salitaaco.defaults.family_voice import TERMS_VERSION
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.tests.users_base import UserBase, make_guardian, sound_upload

ELEVENLABS = "salitaaco.utils.family_voice.ElevenLabs"


class ConsentStepTest(UserBase):
    """Adding a family voice asks for consent first, as a step of its own, before the recording step."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])

    def setUp(self):
        patcher = mock.patch(ELEVENLABS)
        self.elevenlabs = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.elevenlabs.add_voice.return_value = "elevenlabs-boses"
        self.login_as("nanay")

    def test_the_consent_step_comes_before_the_recording_step(self):
        page = self.client.get(reverse("family_voices")).content.decode()

        consent_step = page.index('id="voiceConsentStep"')
        record_step = page.index('id="voiceRecordStep"')
        self.assertLess(consent_step, record_step)
        # The terms, their version and the consent box are in the first step; the recorder is in the second.
        for piece in ["Paalala at Kasunduan sa Boses ng Pamilya", f"bersyon {TERMS_VERSION}", 'name="consent"']:
            self.assertTrue(consent_step < page.index(piece) < record_step, piece)
        for piece in ['id="recordVoiceBtn"', 'id="voiceSampleFile"', 'id="addVoiceSubmit"']:
            self.assertGreater(page.index(piece), record_step, piece)

    def test_the_way_on_is_closed_until_the_terms_are_agreed_to(self):
        response = self.client.get(reverse("family_voices"))
        self.assertContains(response, '<button class="primaryBtn blockBtn formActions" type="button" id="voiceConsentNext" disabled>')

    def test_the_server_refuses_a_recording_sent_without_consent(self):
        response = self.client.post(reverse("family_voices"), {"name": "Lola", "sample": sound_upload()})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kailangang sumang-ayon sa Paalala at Kasunduan")
        self.assertFalse(FamilyVoice.objects.exists())
        self.elevenlabs.add_voice.assert_not_called()

    def test_the_voice_records_when_consent_was_given_and_to_which_terms(self):
        self.client.post(reverse("family_voices"), {"name": "Lola", "consent": "on", "sample": sound_upload()})

        voice = FamilyVoice.objects.get()
        self.assertEqual(voice.consent_version, TERMS_VERSION)
        self.assertIsNotNone(voice.consent_at)
