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
        return {"display_name": "Bagong Bata", "username": "bago", "password": "abcd", **changes}

    def test_valid(self):
        form = RegisterForm(self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_display_name_is_required(self):
        form = RegisterForm(self.valid_data(display_name="  "))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["display_name"], ["Ilagay ang pangalan ng bata / user."])

    def test_password_needs_four_characters(self):
        form = RegisterForm(self.valid_data(password="abc"))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["password"], ["Ang password ay dapat may hindi bababa sa 4 na character."])

    def test_username_must_be_free_ignoring_case(self):
        for username in ["miguel", "MIGUEL"]:
            form = RegisterForm(self.valid_data(username=username))
            self.assertFalse(form.is_valid())
            self.assertEqual(form.errors["username"], ["Ginagamit na ang username na ito."])

    def test_username_is_trimmed(self):
        form = RegisterForm(self.valid_data(username="  bago  "))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["username"], "bago")
