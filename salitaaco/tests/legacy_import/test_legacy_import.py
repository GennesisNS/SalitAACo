from datetime import datetime

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.urls import reverse

from salitaaco.models.customization import Customization
from salitaaco.models.rating import Rating
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.users_base import UserBase, image_bytes
from salitaaco.utils import legacy_import

# Real output of PHP's password_hash("lihim1234", PASSWORD_DEFAULT) (PHP 8.4, cost 12)
# and password_hash("abcd", PASSWORD_BCRYPT, ["cost" => 10]) (the PHP 8.2 default cost).
PHP_HASH_LIHIM1234 = "$2y$12$eYZmZMGdLoUfx3msFE6EuOk4Y7qsgnUzQDG9U8YW0g5sTdA4HTBay"
PHP_HASH_ABCD = "$2y$10$670HC3LJ0dmakYrhUPx9Ze5xan7oH2DyUbGwnbvH5DFZ7vrQEmBx2"


def legacy_user(**changes):
    """A row of the PHP application's `users` table."""
    return {
        "id": 7,
        "username": "luma",
        "password_hash": PHP_HASH_LIHIM1234,
        "display_name": "Lumang User",
        "age": 9,
        "avatar_data": None,
        "avatar_mime": None,
        "is_admin": 0,
        "last_login": datetime(2026, 9, 30, 18, 45, 0),
        "created_at": datetime(2026, 9, 1, 8, 30, 0),
        **changes,
    }


class ImportUserTest(UserBase):
    def test_account_and_profile_are_copied(self):
        user = legacy_import.import_user(legacy_user())

        self.assertEqual(user.username, "luma")
        self.assertEqual(user.profile.display_name, "Lumang User")
        self.assertEqual(user.profile.age, 9)
        self.assertFalse(user.profile.has_avatar)
        self.assertFalse(user.groups.exists())
        # The old wall-clock times are kept, read in the project's time zone (Asia/Manila, UTC+8).
        self.assertEqual(user.date_joined.isoformat(), "2026-09-01T00:30:00+00:00")
        self.assertEqual(user.last_login.isoformat(), "2026-09-30T10:45:00+00:00")

    def test_php_password_still_works_and_is_upgraded_on_login(self):
        legacy_import.import_user(legacy_user())
        self.assertTrue(User.objects.get(username="luma").password.startswith("bcrypt$$2y$12$"))

        self.assertIsNone(authenticate(username="luma", password="maling-password"))
        response = self.client.post(reverse("login"), {"username": "luma", "password": "lihim1234"})
        self.assertRedirects(response, reverse("board"))

        # Django re-hashed it with its own default hasher; the password is unchanged.
        user = User.objects.get(username="luma")
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(user.check_password("lihim1234"))

    def test_hash_from_an_older_php_version_works(self):
        legacy_import.import_user(legacy_user(password_hash=PHP_HASH_ABCD))
        self.assertIsNotNone(authenticate(username="luma", password="abcd"))

    def test_admin_flag_becomes_the_administrator_group(self):
        user = legacy_import.import_user(legacy_user(is_admin=1))
        self.assertTrue(user.groups.filter(name="Administrator").exists())

    def test_avatar_blob_becomes_a_file(self):
        user = legacy_import.import_user(legacy_user(avatar_data=image_bytes("JPEG"), avatar_mime="image/jpeg"))

        self.assertEqual(user.profile.avatar_mime, "image/jpeg")
        self.assertTrue(user.profile.avatar.name.endswith(".jpg"))
        with user.profile.avatar.open("rb") as avatar:
            self.assertEqual(avatar.read(), image_bytes("JPEG"))

    def test_never_logged_in_and_no_age(self):
        user = legacy_import.import_user(legacy_user(last_login=None, age=None))
        self.assertIsNone(user.last_login)
        self.assertIsNone(user.profile.age)

    def test_existing_username_is_skipped(self):
        self.assertIsNone(legacy_import.import_user(legacy_user(username="MIGUEL")))
        self.assertEqual(User.objects.filter(username__iexact="miguel").count(), 1)


class ImportUserDataTest(UserBase):
    def test_customization_blobs_become_files(self):
        customization = legacy_import.import_customization(self.miguel, {
            "word": "mama",
            "image_data": image_bytes(),
            "image_mime": "image/png",
            "sound_data": b"recorded sound",
            "sound_mime": "audio/webm",
            "updated_at": datetime(2026, 9, 2, 12, 0, 0),
        })
        customization.refresh_from_db()

        self.assertEqual((customization.image_mime, customization.sound_mime), ("image/png", "audio/webm"))
        with customization.sound.open("rb") as sound:
            self.assertEqual(sound.read(), b"recorded sound")
        self.assertEqual(customization.updated_at.isoformat(), "2026-09-02T04:00:00+00:00")

    def test_customization_with_only_a_sound(self):
        customization = legacy_import.import_customization(self.miguel, {
            "word": "papa", "image_data": None, "image_mime": None,
            "sound_data": b"recorded sound", "sound_mime": "audio/webm", "updated_at": None,
        })
        self.assertFalse(customization.has_image)
        self.assertTrue(customization.has_sound)

    def test_content_type_of_the_wrong_family_is_not_trusted(self):
        customization = legacy_import.import_customization(self.miguel, {
            "word": "mama", "image_data": b"<script>", "image_mime": "text/html",
            "sound_data": None, "sound_mime": None, "updated_at": None,
        })
        self.assertEqual(customization.image_mime, "application/octet-stream")

    def test_word_usage_and_rating_are_copied(self):
        legacy_import.import_word_usage(self.miguel, {
            "word": "kain", "use_count": 12, "last_used": datetime(2026, 9, 3, 9, 0, 0),
        })
        legacy_import.import_rating(self.miguel, {
            "rating": 4, "comment": "Maganda",
            "created_at": datetime(2026, 9, 4, 9, 0, 0), "updated_at": datetime(2026, 9, 5, 9, 0, 0),
        })

        usage = WordUsage.objects.get(user=self.miguel, word="kain")
        self.assertEqual(usage.use_count, 12)
        self.assertEqual(usage.last_used.isoformat(), "2026-09-03T01:00:00+00:00")

        rating = Rating.objects.get(user=self.miguel)
        self.assertEqual((rating.rating, rating.comment), (4, "Maganda"))
        self.assertEqual(rating.created_at.isoformat(), "2026-09-04T01:00:00+00:00")
        self.assertEqual(rating.updated_at.isoformat(), "2026-09-05T01:00:00+00:00")

    def test_imported_customization_is_served_to_its_owner(self):
        customization = legacy_import.import_customization(self.miguel, {
            "word": "mama", "image_data": image_bytes(), "image_mime": "image/png",
            "sound_data": None, "sound_mime": None, "updated_at": None,
        })
        self.login_as("miguel")

        response = self.client.get(reverse("view_customization_image", args=[customization.uuid]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        response.close()
        self.assertEqual(Customization.objects.filter(user=self.miguel).count(), 1)
