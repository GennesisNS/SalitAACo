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
            "display_name": "Bagong Bata", "username": "bago",
            "password": "Bagong#123", "confirm_password": "Bagong#123", **changes,
        }

    def test_valid(self):
        form = RegisterForm(self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)

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
