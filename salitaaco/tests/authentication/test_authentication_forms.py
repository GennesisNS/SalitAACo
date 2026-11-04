from django.contrib.auth.models import User

from salitaaco.forms.authentication import LoginForm, RegisterForm
from salitaaco.tests.users_base import UserBase


class LoginFormTest(UserBase):
    def test_valid(self):
        form = LoginForm({"username": "miguel", "password": "lihim1234"})
        self.assertTrue(form.is_valid())

    def test_username_and_password_are_required(self):
        form = LoginForm({"username": "", "password": ""})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["username"], ["Ilagay ang username."])
        self.assertEqual(form.errors["password"], ["Ilagay ang password."])


class RegisterFormTest(UserBase):
    def valid_data(self, **changes):
        return {
            "display_name": "Bagong Bata", "email": "bago@example.com", "age": "35", "username": "bago",
            "password": "Bagong#123", "confirm_password": "Bagong#123", "privacy_consent": "on", **changes,
        }

    def test_valid(self):
        form = RegisterForm(self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_email_age_and_privacy_consent_are_required(self):
        form = RegisterForm(self.valid_data(email="", age="", privacy_consent=""))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["email"], ["Ilagay ang email mo."])
        self.assertEqual(form.errors["age"], ["Ilagay ang edad mo."])
        self.assertEqual(form.errors["privacy_consent"], ["Kailangang sumang-ayon sa Paalala sa Privacy para makagawa ng account."])

    def test_email_must_be_an_email_address(self):
        for email in ["bago", "bago@", "bago example.com"]:
            self.assertEqual(RegisterForm(self.valid_data(email=email)).errors["email"], ["Hindi tama ang email address."], email)

    def test_email_must_be_free_ignoring_case(self):
        User.objects.filter(username="miguel").update(email="miguel@example.com")
        for email in ["miguel@example.com", "MIGUEL@Example.com"]:
            self.assertEqual(RegisterForm(self.valid_data(email=email)).errors["email"], ["May account na ang email na ito."], email)

    def test_a_guardian_is_18_or_older(self):
        self.assertTrue(RegisterForm(self.valid_data(age="18")).is_valid())
        for age, error in [
            ("17", "18 taong gulang pataas lang ang puwedeng gumawa ng account."),
            ("121", "Hindi tama ang edad."),
            ("tatlumpu", "Hindi tama ang edad."),
        ]:
            self.assertEqual(RegisterForm(self.valid_data(age=age)).errors["age"], [error], age)

    def test_display_name_is_required(self):
        form = RegisterForm(self.valid_data(display_name="  "))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["display_name"], ["Ilagay ang pangalan mo."])

    def test_passwords_must_match(self):
        form = RegisterForm(self.valid_data(confirm_password="Iba#12345"))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["confirm_password"], ["Hindi magkatugma ang password at kumpirmasyon."])

    def test_password_must_be_strong(self):
        cases = [
            ("Bago#12", "Hindi bababa sa 8 character ang password."),
            ("Bagong#123" + "a" * 120, "Hanggang 128 character lang ang password."),
            ("bagong#123", "Kailangang may kahit isang malaking titik ang password."),
            ("BAGONG#123", "Kailangang may kahit isang maliit na titik ang password."),
            ("Bagong#abc", "Kailangang may kahit isang numero ang password."),
            ("Bagong1234", "Kailangang may kahit isang espesyal na character ang password (hal. ! @ # $)."),
        ]
        for password, error in cases:
            form = RegisterForm(self.valid_data(password=password, confirm_password=password))
            self.assertFalse(form.is_valid(), password)
            self.assertEqual(form.errors["password"], [error])

    def test_username_must_be_free_ignoring_case(self):
        for username in ["miguel", "MIGUEL"]:
            form = RegisterForm(self.valid_data(username=username))
            self.assertFalse(form.is_valid())
            self.assertEqual(form.errors["username"], ["Ginagamit na ang username na ito."])

    def test_username_is_trimmed(self):
        form = RegisterForm(self.valid_data(username="  bago  "))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["username"], "bago")

    def test_a_username_is_letters_numbers_and_dot_dash_underscore(self):
        for username in ["bago", "maria.santos", "juan_dela-cruz", "nanay2026"]:
            self.assertTrue(RegisterForm(self.valid_data(username=username)).is_valid(), username)
        for username, error in [
            ("ab", "Hindi bababa sa 3 character ang username."),
            ("maria santos", "Mga titik, numero, tuldok (.), gitling (-) at underscore (_) lang ang puwede sa username, walang espasyo."),
            ("niño", "Mga titik, numero, tuldok (.), gitling (-) at underscore (_) lang ang puwede sa username, walang espasyo."),
            ("<script>", "Mga titik, numero, tuldok (.), gitling (-) at underscore (_) lang ang puwede sa username, walang espasyo."),
        ]:
            self.assertEqual(RegisterForm(self.valid_data(username=username)).errors["username"], [error], username)

    def test_a_name_is_written_as_filipinos_write_names(self):
        for name in ["Maria Santos", "Ma. Teresa Dela Cruz-Reyes", "Niño", "José D'Souza", "Sto. Tomas Jr."]:
            self.assertTrue(RegisterForm(self.valid_data(display_name=name)).is_valid(), name)
        error = "Mga titik, espasyo, gitling (-), kudlit (') at tuldok (.) lang ang puwede sa pangalan."
        for name in ["Maria2", "<b>Maria</b>", ".Maria", "Maria!"]:
            self.assertEqual(RegisterForm(self.valid_data(display_name=name)).errors["display_name"], [error], name)
