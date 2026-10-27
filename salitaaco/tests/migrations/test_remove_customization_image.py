import os
import shutil
import tempfile

from django.core.files.base import ContentFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, override_settings

from salitaaco.tests.users_base import image_bytes, remove_default_users

BEFORE = [("salitaaco", "0028_plan_family_voice_limit")]
AFTER = [("salitaaco", "0029_remove_customization_image")]


def migrate(target):
    """Migrate the test database to `target` and return the models as they are at that point."""
    executor = MigrationExecutor(connection)
    executor.migrate(target)
    return MigrationExecutor(connection).loader.project_state(target).apps


class RemoveCustomizationImageTest(TransactionTestCase):
    """Migration 0029 deletes the tiles' own pictures and their files, and keeps the recordings."""

    def setUp(self):
        media_root = tempfile.mkdtemp(prefix="salitaaco-test-media-")
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        media = override_settings(MEDIA_ROOT=media_root)
        media.enable()
        self.addCleanup(media.disable)
        # Whatever happens, leave the schema at the latest migration for the tests that run next.
        self.addCleanup(lambda: migrate(MigrationExecutor(connection).loader.graph.leaf_nodes()))
        remove_default_users()

    def test_pictures_go_with_their_files_and_recordings_stay(self):
        apps = migrate(BEFORE)
        User = apps.get_model("auth", "User")
        Customization = apps.get_model("salitaaco", "Customization")
        miguel = User.objects.create(username="miguel", password="x")

        both = Customization.objects.create(user=miguel, word="mama")
        both.image.save("larawan.png", ContentFile(image_bytes()), save=False)
        both.sound.save("tunog.webm", ContentFile(b"tunog"), save=False)
        both.save()
        only_picture = Customization.objects.create(user=miguel, word="papa")
        only_picture.image.save("larawan2.png", ContentFile(image_bytes()))
        picture_paths = [both.image.path, only_picture.image.path]
        sound_path = both.sound.path

        apps = migrate(AFTER)
        Customization = apps.get_model("salitaaco", "Customization")

        self.assertEqual(list(Customization.objects.values_list("word", flat=True)), ["mama"])
        for path in picture_paths:
            self.assertFalse(os.path.exists(path), path)
        self.assertTrue(os.path.exists(sound_path))
        self.assertNotIn("image", [field.name for field in Customization._meta.get_fields()])
