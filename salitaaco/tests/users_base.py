import io
import shutil
import tempfile

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from salitaaco.models.admin_account import AdminAccount
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.guardian_account import GuardianAccount

GROUPS = ["Administrator", "Guardian", "Child"]

# Each user gets the account model and the group of their role.
USERS = [
    {"username": "miguel", "password": "lihim1234", "display_name": "Miguel", "age": 7, "role": "Child"},
    {"username": "ana", "password": "ana-password", "display_name": "Ana", "age": None, "role": "Child"},
    {"username": "developer", "password": "dev-password", "display_name": "Developer", "role": "Administrator"},
]

GUARDIAN_PASSWORD = "nanay-password"


def image_bytes(image_format="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "orange").save(buffer, image_format)
    return buffer.getvalue()


def image_upload(name="larawan.png", image_format="PNG", content_type="image/png", padding=0):
    """An uploaded picture. `padding` adds bytes after the image data to make the file bigger."""
    return SimpleUploadedFile(name, image_bytes(image_format) + b"\0" * padding, content_type=content_type)


def sound_upload(name="sound.webm", content_type="audio/webm", size=64):
    return SimpleUploadedFile(name, b"\x1a\x45\xdf\xa3" + b"\0" * size, content_type=content_type)


def make_guardian(username, display_name, children=()):
    """A guardian account, made the guardian of the given users' child accounts."""
    user = User.objects.create_user(username=username, password=GUARDIAN_PASSWORD)
    user.groups.add(Group.objects.get_or_create(name="Guardian")[0])
    guardian = GuardianAccount.objects.create(user=user, display_name=display_name)
    ChildAccount.objects.filter(user__in=children).update(guardian=guardian)
    return guardian


class UserBase(TestCase):
    """
    Base for feature tests: two children (neither has a guardian yet) and one
    administrator, and a temporary media folder so uploads made by tests never
    touch the real one. Tests about guardians add one with make_guardian().
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
            user.groups.add(Group.objects.get(name=data["role"]))
            if data["role"] == "Administrator":
                AdminAccount.objects.create(user=user, display_name=data["display_name"])
            else:
                ChildAccount.objects.create(user=user, display_name=data["display_name"], age=data["age"])
            cls.users[data["username"]] = user

        cls.miguel = cls.users["miguel"]
        cls.ana = cls.users["ana"]
        cls.developer = cls.users["developer"]

    def login_as(self, username):
        """Log in as one of the base users, or as a guardian made with make_guardian()."""
        data = next((user for user in USERS if user["username"] == username), None)
        password = data["password"] if data else GUARDIAN_PASSWORD
        self.assertTrue(self.client.login(username=username, password=password))
        return User.objects.get(username=username)
