from salitaaco.forms.children.create_child import CreateChildForm
from salitaaco.forms.children.delete_child import DeleteChildForm
from salitaaco.forms.children.reset_child_password import ResetChildPasswordForm
from salitaaco.tests.users_base import GUARDIAN_PASSWORD, UserBase, make_guardian


class CreateChildFormTest(UserBase):
    def valid_data(self, **changes):
        return {
            "display_name": "Bunso", "username": "bunso", "age": "5",
            "password": "Bunso#123", "confirm_password": "Bunso#123", **changes,
        }

    def test_valid_with_and_without_age(self):
        form = CreateChildForm(self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["age"], 5)

        form = CreateChildForm(self.valid_data(age=""))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["age"])

    def test_name_and_username_are_required(self):
        form = CreateChildForm(self.valid_data(display_name=" ", username=" "))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["display_name"], ["Ilagay ang pangalan ng bata."])
        self.assertEqual(form.errors["username"], ["Ilagay ang username ng bata."])

    def test_username_must_be_free_ignoring_case(self):
        form = CreateChildForm(self.valid_data(username="MIGUEL"))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["username"], ["Ginagamit na ang username na ito."])

    def test_age_must_be_from_0_to_150(self):
        for age in ["-1", "151", "lima"]:
            form = CreateChildForm(self.valid_data(age=age))
            self.assertFalse(form.is_valid(), age)
            self.assertEqual(form.errors["age"], ["Hindi tama ang edad."])

    def test_password_must_be_strong_and_match(self):
        form = CreateChildForm(self.valid_data(password="mahina", confirm_password="mahina"))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["password"], ["Password must be at least 8 characters long."])

        form = CreateChildForm(self.valid_data(confirm_password="Iba#12345"))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["confirm_password"], ["Hindi magkatugma ang password at kumpirmasyon."])


class ResetChildPasswordFormTest(UserBase):
    def test_valid(self):
        form = ResetChildPasswordForm({"new_password": "Bago#1234", "confirm_password": "Bago#1234"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_must_be_strong_and_match(self):
        form = ResetChildPasswordForm({"new_password": "bagong#123", "confirm_password": "bagong#123"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["new_password"], ["Password must contain at least one uppercase letter."])

        form = ResetChildPasswordForm({"new_password": "Bago#1234", "confirm_password": "Iba#12345"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["confirm_password"], ["Hindi magkatugma ang bagong password at kumpirmasyon."])


class DeleteChildFormTest(UserBase):
    def test_needs_the_guardians_own_password(self):
        guardian = make_guardian("nanay", "Nanay Rosa", children=[self.miguel])

        self.assertTrue(DeleteChildForm({"password": GUARDIAN_PASSWORD}, guardian_user=guardian.user).is_valid())

        # The child's password does not confirm it.
        form = DeleteChildForm({"password": "lihim1234"}, guardian_user=guardian.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["password"], ["Maling password."])

        form = DeleteChildForm({"password": ""}, guardian_user=guardian.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["password"], ["Ilagay ang password mo para kumpirmahin."])
