from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils import timezone

from salitaaco.defaults.family_voice import TERMS_VERSION
from salitaaco.defaults.plans import PLUS
from salitaaco.models.added_word import AddedWord
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.customization import Customization
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.generated_report import GeneratedReport
from salitaaco.models.guardian_board import GuardianBoard
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.plan import Plan
from salitaaco.models.support_message import SupportMessage
from salitaaco.tests.payments_base import make_payment, set_gcash_qr
from salitaaco.tests.users_base import UserBase, image_bytes, make_guardian
from salitaaco.utils.plans import approve_payment

# Each role, and nobody logged in.
ROLES = [None, "miguel", "nanay", "developer"]

# Pages that take a form, sent empty: each says what is missing, never fails.
FORM_PAGES = [
    "login", "register", "board", "profile", "settings", "children", "family_voices", "guardian_words", "support",
    "plan", "reports", "generated_reports", "users", "admin_boards", "set_board_status", "words", "feedback",
    "system_general", "system_plans", "system_access", "system_privacy", "subscriptions", "increment_word_usage",
    "record_board_open",
]


def project_route_names():
    """The names of the project's own routes, not Django's admin site."""
    names = set()

    def walk(patterns, prefix=""):
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                walk(pattern.url_patterns, prefix + str(pattern.pattern))
            elif isinstance(pattern, URLPattern) and pattern.name and not prefix.startswith("admin/"):
                names.add(pattern.name)

    walk(get_resolver().url_patterns)
    return names


@override_settings(ELEVENLABS_API_KEY="", ELEVENLABS_VOICE_ID="")
class EveryRouteTest(UserBase):
    """
    Every route of the app, opened by each role and by nobody: none of them
    fails with a server error, whatever the role is allowed to see. The
    guardian (Nanay, on Plus) has one of everything that has its own address.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        child = ChildAccount.objects.get(user=cls.miguel)
        approve_payment(make_payment(nanay), cls.developer)
        payment = make_payment(nanay)
        set_gcash_qr()

        def picture(thing):
            thing.set_icon_image("larawan.png", ContentFile(image_bytes()), "image/png")
            return thing

        board = picture(GuardianBoard.objects.create(guardian=nanay, name="Bahay ni Lola", emoji="🏡"))
        guardian_word = picture(GuardianWord.objects.create(guardian=nanay, board=board.name, word="Kuya Jun", emoji="👦"))
        added_word = picture(AddedWord.objects.create(board="Pagkain", word="pandesal", emoji="🥖"))
        customization = Customization.objects.create(user=cls.miguel, word="kain")
        customization.set_sound("tunog.webm", ContentFile(b"\x1a\x45\xdf\xa3" + b"\0" * 64), "audio/webm")
        child.set_avatar("mukha.png", ContentFile(image_bytes()), "image/png")
        voice = FamilyVoice.objects.create(
            guardian=nanay, name="Lola", elevenlabs_voice_id="boses-lola", consent_at=timezone.now(), consent_version=TERMS_VERSION,
        )
        message = SupportMessage.objects.create(guardian=nanay, message="Tulong po.")
        report = GeneratedReport.objects.create(
            report_type="users", file_type="csv", start_date=timezone.localdate(), end_date=timezone.localdate(),
            file=ContentFile(b"Ulat", name="ulat.csv"), generated_by=cls.developer,
        )

        cls.route_args = {
            "view_customization_sound": [customization.uuid],
            "reset_customization": [customization.uuid],
            "manage_child": [child.uuid],
            "view_child_avatar": [child.uuid],
            "remove_child_avatar": [child.uuid],
            "child_board": [child.uuid],
            "child_boards": [child.uuid],
            "remove_own_board": [child.uuid, board.uuid],
            "child_voice": [child.uuid],
            "child_usage": [child.uuid],
            "generate_family_voice": [voice.uuid],
            "remove_family_voice": [voice.uuid],
            "play_family_voice_word": [voice.uuid, "kain"],
            "guardian_board_icon": [board.uuid],
            "remove_guardian_word": [guardian_word.uuid],
            "voice_guardian_word": [guardian_word.uuid],
            "play_guardian_word": [guardian_word.uuid],
            "guardian_word_image": [guardian_word.uuid],
            "view_payment_proof": [payment.uuid],
            "set_user_status": [cls.miguel.pk],
            "edit_word": [added_word.uuid],
            "delete_word": [added_word.uuid],
            "added_word_image": [added_word.uuid],
            "resolve_support_message": [message.uuid],
            "remove_plan": [Plan.objects.get(key=PLUS).pk],
            "remove_admin": [cls.developer.pk],
            "approve_payment": [payment.uuid],
            "view_generated_report": [report.uuid],
            "remove_generated_report": [report.uuid],
        }

    def url(self, name):
        return reverse(name, args=self.route_args.get(name, []))

    def as_each_role(self):
        for role in ROLES:
            self.client.logout()
            if role:
                self.client.force_login(User.objects.get(username=role))
            yield role

    def test_every_route_is_listed_here(self):
        names = project_route_names()
        self.assertGreater(len(names), 60)
        self.assertTrue({"index", "login", "board", "child_boards", "approve_payment"} <= names)
        # A new route with an address of its own needs its sample here, so that it is opened too.
        for name in names:
            try:
                self.url(name)
            except Exception as error:  # NoReverseMatch, said with the route's name
                self.fail(f"{name}: {error}")

    def test_every_route_opens_for_every_role_without_a_server_error(self):
        for role in self.as_each_role():
            for name in sorted(project_route_names()):
                with self.subTest(role=role, route=name):
                    response = self.client.get(self.url(name))
                    self.assertLess(response.status_code, 500)

    def test_every_form_page_sent_empty_says_what_is_missing(self):
        for role in self.as_each_role():
            for name in FORM_PAGES:
                with self.subTest(role=role, route=name):
                    response = self.client.post(self.url(name), {})
                    self.assertLess(response.status_code, 500)
