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
            ("Bago#12", "Password must be at least 8 characters long."),
            ("bagong#123", "Password must contain at least one uppercase letter."),
            ("BAGONG#123", "Password must contain at least one lowercase letter."),
            ("Bagong#abc", "Password must contain at least one number."),
            ("Bagong1234", "Password must contain at least one special character."),
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
