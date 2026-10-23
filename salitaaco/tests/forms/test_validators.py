from django import forms
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from salitaaco.forms.account.profile_information import ProfileInformationForm
from salitaaco.forms.helpers import BaseForm
from salitaaco.forms.system.general_settings import GeneralSettingsForm
from salitaaco.forms.validators import check_tile_word, validate_phone_number


class PhoneNumberTest(SimpleTestCase):
    def test_numbers_as_people_write_them(self):
        for number in ["09170000000", "0917 000 0000", "+63 917 000 0000", "(02) 8123-4567"]:
            validate_phone_number(number)

    def test_letters_and_numbers_too_short_or_long_are_not(self):
        for number, error in [
            ("tawagan mo ako", "Mga numero lang ang puwede, hal. 0917 000 0000."),
            ("0917-ABC", "Mga numero lang ang puwede, hal. 0917 000 0000."),
            ("12345", "Hindi tama ang haba ng numero (7 hanggang 15 digit)."),
            ("1" * 16, "Hindi tama ang haba ng numero (7 hanggang 15 digit)."),
        ]:
            with self.assertRaisesMessage(ValidationError, error):
                validate_phone_number(number)

    def test_the_support_phone_is_checked(self):
        self.assertEqual(GeneralSettingsForm({"contact_phone": "tawagan mo ako"}).errors["contact_phone"],
                         ["Mga numero lang ang puwede, hal. 0917 000 0000."])
        self.assertTrue(GeneralSettingsForm({"contact_phone": ""}).is_valid())


class TileWordTest(SimpleTestCase):
    def test_a_word_of_the_boards_or_nothing_to_check(self):
        self.assertEqual(check_tile_word("isda", {"isda"}), "isda")
        self.assertEqual(check_tile_word("kahit ano", None), "kahit ano")
        with self.assertRaisesMessage(ValidationError, "Walang ganitong tile sa board."):
            check_tile_word("kahit ano", {"isda"})


class ProfileNameTest(SimpleTestCase):
    def test_a_changed_name_follows_the_same_rule_as_signing_up(self):
        self.assertTrue(ProfileInformationForm({"display_name": "Ma. Niña Reyes"}, include_age=False).is_valid())
        form = ProfileInformationForm({"display_name": "<b>Miguel</b>"}, include_age=False)
        self.assertEqual(form.errors["display_name"],
                         ["Mga titik, espasyo, gitling (-), kudlit (') at tuldok (.) lang ang puwede sa pangalan."])


class FilipinoMessagesTest(SimpleTestCase):
    """A field that does not say its own error message says Django's in Filipino, not in English."""

    class SampleForm(BaseForm):
        name = forms.CharField(max_length=5)
        count = forms.IntegerField(min_value=1, max_value=3)
        kind = forms.ChoiceField(choices=[("a", "A")])
        note = forms.CharField(required=True, max_length=5, error_messages={"required": "Sariling mensahe."})

    def test_django_messages_are_said_in_filipino(self):
        form = self.SampleForm({"name": "masyadong mahaba", "count": "9", "kind": "z"})
        self.assertEqual(form.errors["name"], ["Masyadong mahaba (hanggang 5 character)."])
        self.assertEqual(form.errors["count"], ["Hanggang 3 lang."])
        self.assertEqual(form.errors["kind"], ["Pumili mula sa listahan."])
        self.assertEqual(self.SampleForm({"count": "0"}).errors["count"], ["Hindi bababa sa 1."])
        self.assertEqual(self.SampleForm({}).errors["name"], ["Kailangang sagutan ito."])

    def test_a_forms_own_message_is_kept(self):
        self.assertEqual(self.SampleForm({}).errors["note"], ["Sariling mensahe."])
