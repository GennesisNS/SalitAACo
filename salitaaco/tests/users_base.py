import io
import shutil
import tempfile

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from salitaaco.models.profile import Profile

GROUPS = ["Administrator"]

USERS = [
    {"username": "miguel", "password": "lihim1234", "display_name": "Miguel", "age": 7, "groups": []},
    {"username": "ana", "password": "ana-password", "display_name": "Ana", "age": None, "groups": []},
    {"username": "developer", "password": "dev-password", "display_name": "Developer", "age": 30, "groups": ["Administrator"]},
]


def image_bytes(image_format="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "orange").save(buffer, image_format)
    return buffer.getvalue()


def image_upload(name="larawan.png", image_format="PNG", content_type="image/png", padding=0):
    """An uploaded picture. `padding` adds bytes after the image data to make the file bigger."""
    return SimpleUploadedFile(name, image_bytes(image_format) + b"\0" * padding, content_type=content_type)


def sound_upload(name="sound.webm", content_type="audio/webm", size=64):
    return SimpleUploadedFile(name, b"\x1a\x45\xdf\xa3" + b"\0" * size, content_type=content_type)


class UserBase(TestCase):
    """
    Base for feature tests: two ordinary users and one administrator, and a
    temporary media folder so uploads made by tests never touch the real one.
    """

    @classmethod
    def setUpClass(cls):
        cls.media_root = tempfile.mkdtemp(prefix="salitaaco-test-media-")
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_root)
        cls.media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.media_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        for name in GROUPS:
            Group.objects.get_or_create(name=name)

        cls.users = {}
        for data in USERS:
            user = User.objects.create_user(username=data["username"], password=data["password"])
            user.groups.set(Group.objects.filter(name__in=data["groups"]))
            Profile.objects.create(user=user, display_name=data["display_name"], age=data["age"])
            cls.users[data["username"]] = user

        cls.miguel = cls.users["miguel"]
        cls.ana = cls.users["ana"]
        cls.developer = cls.users["developer"]

    def login_as(self, username):
        data = next(user for user in USERS if user["username"] == username)
        self.assertTrue(self.client.login(username=data["username"], password=data["password"]))
        return self.users[username]
