from salitaaco.forms.account.change_password import ChangePasswordForm
from salitaaco.forms.account.delete_account import DeleteAccountForm
from salitaaco.forms.account.profile_information import ProfileInformationForm
from salitaaco.forms.account.upload_avatar import UploadAvatarForm
from salitaaco.tests.users_base import UserBase, image_upload
from salitaaco.utils.uploads import MAX_UPLOAD_SIZE


class ProfileInformationFormTest(UserBase):
    def test_valid_with_and_without_age(self):
        form = ProfileInformationForm({"display_name": " Miguel ", "age": "7"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data, {"display_name": "Miguel", "age": 7})

        form = ProfileInformationForm({"display_name": "Miguel", "age": ""})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["age"])

    def test_display_name_is_required(self):
        form = ProfileInformationForm({"display_name": "  ", "age": ""})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["display_name"], ["Ilagay ang pangalan."])

    def test_age_must_be_a_whole_number_from_0_to_150(self):
        for age in ["-1", "151", "pito", "7.5"]:
            form = ProfileInformationForm({"display_name": "Miguel", "age": age})
            self.assertFalse(form.is_valid(), age)
            self.assertEqual(form.errors["age"], ["Hindi tama ang edad."])


class UploadAvatarFormTest(UserBase):
    def test_valid_types(self):
        for image_format, content_type in [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp"), ("GIF", "image/gif")]:
            form = UploadAvatarForm({}, {"avatar": image_upload(image_format=image_format, content_type=content_type)})
            self.assertTrue(form.is_valid(), form.errors)

    def test_missing_unsupported_and_too_large(self):
        cases = [
            ({}, "Walang natanggap na larawan."),
            ({"avatar": image_upload(image_format="BMP", content_type="image/bmp")}, "Hindi suportadong file type ng larawan."),
            ({"avatar": image_upload(padding=MAX_UPLOAD_SIZE)}, "Masyadong malaki ang larawan (max 5MB)."),
        ]
        for files, error in cases:
            form = UploadAvatarForm({}, files)
            self.assertFalse(form.is_valid())
            self.assertEqual(form.errors["avatar"], [error])


class ChangePasswordFormTest(UserBase):
    def form(self, **changes):
        data = {"current_password": "lihim1234", "new_password": "Bagong#123", "confirm_password": "Bagong#123", **changes}
        return ChangePasswordForm(data, user=self.miguel)

    def test_valid(self):
        self.assertTrue(self.form().is_valid())

    def test_wrong_current_password(self):
        form = self.form(current_password="mali")
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["current_password"], ["Maling kasalukuyang password."])

    def test_new_password_must_be_strong(self):
        form = self.form(new_password="Bago#12", confirm_password="Bago#12")
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["new_password"], ["Password must be at least 8 characters long."])

    def test_confirmation_must_match(self):
        form = self.form(confirm_password="iba")
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["confirm_password"], ["Hindi magkatugma ang bagong password at kumpirmasyon."])


class DeleteAccountFormTest(UserBase):
    def test_valid(self):
        self.assertTrue(DeleteAccountForm({"password": "lihim1234"}, user=self.miguel).is_valid())

    def test_password_is_required_and_must_be_right(self):
        form = DeleteAccountForm({"password": ""}, user=self.miguel)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["password"], ["Ilagay ang password para kumpirmahin."])

        form = DeleteAccountForm({"password": "mali"}, user=self.miguel)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["password"], ["Maling password."])
