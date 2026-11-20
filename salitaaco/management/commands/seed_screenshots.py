"""
Fills the screenshot database (screenshots.sqlite3) with made-up, realistic
data for screenshots/capture.py: admins, guardians on Free and on Plus, their
children, 90 days of usage, payments, ratings, support messages, a family's
own boards, tiles and voices, and three generated reports.

It only ever runs against a database file named screenshots.sqlite3, and only
writes uploads to a MEDIA_ROOT other than the real media/ folder. Nothing is
sent to ElevenLabs: the family's tiles and voices are made with the ORM, and
the voices' words are copies of the app's shared-voice MP3s in static/.

    DB_ENGINE=sqlite DB_NAME=screenshots.sqlite3 MEDIA_ROOT=<repo>/screenshots/_media \
        python manage.py seed_screenshots --reset
"""
import random
import shutil
from datetime import datetime, time, timedelta
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from salitaaco.defaults.administrator_roles import ADMINISTRATOR
from salitaaco.defaults.family_voice import PREVIEW_WORD, TERMS_VERSION
from salitaaco.defaults.plans import APPROVED, FREE, PENDING, PLUS, REJECTED
from salitaaco.defaults.privacy import PRIVACY_TERMS_VERSION
from salitaaco.defaults.reports import (
    CSV,
    FEEDBACK,
    MESSAGE_COLUMNS,
    PAYMENT_COLUMNS,
    PAYMENTS,
    PRINTABLE,
    RATING_COLUMNS,
    USER_COLUMNS,
    USERS,
)
from salitaaco.defaults.user_roles import CHILD, GUARDIAN
from salitaaco.defaults.vocabulary import CATEGORIES
from salitaaco.models.added_word import AddedWord
from salitaaco.models.admin_account import AdminAccount
from salitaaco.models.board_status import BoardStatus
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.customization import Customization
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.guardian_board import GuardianBoard
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan
from salitaaco.models.rating import Rating
from salitaaco.models.site_setting import SiteSetting
from salitaaco.models.support_message import SupportMessage
from salitaaco.models.word_usage import WordUsage
from salitaaco.utils.account import add_to_group
from salitaaco.utils.family_voice import family_voice_directory, family_voice_words
from salitaaco.utils.guardian_words import guardian_word_audio_path
from salitaaco.utils.plans import add_months
from salitaaco.utils.tile_audio import VERB_ASPECTS, tile_audio_directory, tile_audio_file_name
from salitaaco.utils.uploads import random_upload_name

DATABASE_FILE = "screenshots.sqlite3"
PASSWORD = "Salita#2026"
DAYS = 90
EMAIL_DOMAIN = "example.com"

# The placeholder accounts migration 0027 makes; they would only clutter the lists.
PLACEHOLDER_USERNAMES = ["admin@example.com", "guardian@example.com", "child@example.com"]

# (username, name, joined days ago, has a picture). The first is the demo admin.
ADMINS = [
    ("andrea.villanueva", "Andrea Villanueva", 89, True),
    ("paolo.mendoza", "Paolo Mendoza", 72, True),
    ("kristine.bautista", "Kristine Bautista", 23, False),
]

# What became of each guardian's payments:
#   plus      on SalitAACo Plus now, by a chain of approved monthly payments
#   lapsed    paid before, but the months ran out: back on Free
#   pending   on Free, with a payment waiting for an admin
#   rejected  on Free, their payment was turned down
#   free      never paid
# (username, name, age, joined days ago, plan story, active, has a picture,
#  children as (name, username, age)). The first is the demo guardian.
GUARDIANS = [
    ("maricel.santos", "Maricel Santos", 36, 86, "plus", True, True,
     [("Miguel Santos", "migo.santos", 7), ("Sofia Santos", "sofia.santos", 5), ("Tomas Santos", "tomas.santos", 10)]),
    ("joel.dizon", "Joel Dizon", 41, 84, "plus", True, True,
     [("Gab Dizon", "gab.dizon", 8), ("Ella Dizon", "ella.dizon", 6)]),
    ("rowena.garcia", "Rowena Garcia", 38, 80, "plus", True, False, [("Enzo Garcia", "enzo.garcia", 9)]),
    ("arnel.cruz", "Arnel Cruz", 45, 77, "lapsed", True, False, [("Bianca Cruz", "bianca.cruz", 11)]),
    ("liza.mercado", "Liza Mercado", 33, 74, "plus", True, True,
     [("Yuan Mercado", "yuan.mercado", 4), ("Kaye Mercado", "kaye.mercado", 7), ("Lito Mercado", "lito.mercado", 10)]),
    ("ramon.aquino", "Ramon Aquino", 50, 70, "free", True, False, [("Andrei Aquino", "andrei.aquino", 12)]),
    ("cristina.lopez", "Cristina Lopez", 29, 66, "pending", True, False, [("Mika Lopez", "mika.lopez", 5)]),
    ("dennis.ramos", "Dennis Ramos", 39, 63, "plus", True, False,
     [("Carlo Ramos", "carlo.ramos", 6), ("Jasmine Ramos", "jasmine.ramos", 8)]),
    ("ana.delarosa", "Ana Dela Rosa", 34, 60, "free", True, True, [("Pia Dela Rosa", "pia.delarosa", 6)]),
    ("ricardo.flores", "Ricardo Flores", 47, 57, "lapsed", False, False, [("Nico Flores", "nico.flores", 13)]),
    ("glenda.torres", "Glenda Torres", 42, 54, "plus", True, False,
     [("Ivan Torres", "ivan.torres", 9), ("Lea Torres", "lea.torres", 5)]),
    ("mark.gonzales", "Mark Gonzales", 31, 50, "rejected", True, False, [("Jomar Gonzales", "jomar.gonzales", 7)]),
    ("teresa.navarro", "Teresa Navarro", 55, 47, "free", True, False, [("Angelo Navarro", "angelo.navarro", 8)]),
    ("vilma.castillo", "Vilma Castillo", 37, 44, "plus", True, False,
     [("Chloe Castillo", "chloe.castillo", 4), ("Lance Castillo", "lance.castillo", 10)]),
    ("edwin.pascual", "Edwin Pascual", 44, 40, "pending", True, False, [("Rafael Pascual", "rafael.pascual", 9)]),
    ("lorna.bernardo", "Lorna Bernardo", 52, 38, "rejected", False, False, [("Kyle Bernardo", "kyle.bernardo", 12)]),
    ("jocelyn.morales", "Jocelyn Morales", 35, 36, "free", False, False, [("Trisha Morales", "trisha.morales", 6)]),
    ("benjie.salazar", "Benjie Salazar", 40, 32, "plus", True, False, [("Kian Salazar", "kian.salazar", 5)]),
    ("rosario.domingo", "Rosario Domingo", 48, 48, "lapsed", True, False,
     [("Bea Domingo", "bea.domingo", 11), ("Marco Domingo", "marco.domingo", 7)]),
    ("allan.manalo", "Allan Manalo", 32, 24, "pending", True, False, [("Zia Manalo", "zia.manalo", 4)]),
    ("irene.sison", "Irene Sison", 30, 19, "free", True, False, [("Elijah Sison", "elijah.sison", 6)]),
    ("noel.fernandez", "Noel Fernandez", 43, 14, "plus", True, False,
     [("Sam Fernandez", "sam.fernandez", 8), ("Ria Fernandez", "ria.fernandez", 10)]),
    ("grace.valdez", "Grace Valdez", 28, 9, "free", True, False, [("Lucas Valdez", "lucas.valdez", 3)]),
    ("jerome.padilla", "Jerome Padilla", 37, 5, "free", True, False, [("Aya Padilla", "aya.padilla", 5)]),
    ("melanie.robles", "Melanie Robles", 34, 2, "pending", True, False, [("Gelo Robles", "gelo.robles", 7)]),
    ("carmela.ocampo", "Carmela Ocampo", 39, 0, "free", True, False, [("Jairus Ocampo", "jairus.ocampo", 6)]),
]

# Words children reach for most. Every other tile word weighs 1.
POPULAR_WORDS = {
    "gusto ko": 14, "oo": 11, "hindi": 10, "kumain": 9, "mama": 9, "uminom": 8, "salamat": 8,
    "kakain": 7, "gutom": 7, "ayaw ko": 6, "masaya": 6, "tulong": 6, "banyo": 6, "maglalaro": 6,
    "papa": 5, "naglaro": 5, "uhaw": 5, "opo": 5, "matutulog": 4, "pagod": 4, "lola": 4,
    "isda": 3, "prutas": 3, "bahay": 3, "po": 3, "masakit": 3, "ate": 3, "kuya": 3,
}
BOARD_WEIGHTS = {"Pagkain": 8, "Pakiramdam": 7, "Tao": 6, "Pandiwa": 5, "Bagay": 4, "Lugar": 3}

# An admin's additions to the vocabulary.
ADDED_WORDS = [
    ("Pagkain", "tinapay", "🍞", 64),
    ("Pagkain", "gatas", "🥛", 51),
    ("Bagay", "tubig", "🚰", 33),
    ("Pakiramdam", "inaantok", "🥱", 12),
]
# The board an admin hid from everyone, and how many days ago; it was used before then.
HIDDEN_BOARD = "Lugar"
HIDDEN_BOARD_DAYS_AGO = 15

# The demo family's own boards and tiles: (board, emoji, made days ago, [(word, emoji)]).
DEMO_BOARDS = [
    ("Pamilya Namin", "🏡", 70, [("Lola Remy", "👵"), ("Tito Boy", "🧔"), ("si Bantay", "🐶")]),
    ("Sa Paaralan", "🎒", 55, [("Teacher Joy", "👩‍🏫"), ("baon", "🍱"), ("recess", "🔔")]),
    ("Laruan", "🧸", 30, [("bola", "🏀"), ("krayola", "🖍️")]),
]
DEMO_APP_BOARD_WORDS = [("Pagkain", "sinigang", "🍲", 40)]
# A child's boards their guardian turned off: (child username, board).
DEMO_HIDDEN_BOARDS = [("sofia.santos", "Sa Paaralan"), ("sofia.santos", "Pandiwa"), ("tomas.santos", "Laruan")]
# The demo family's voices: (name, made days ago, children who hear it).
DEMO_VOICES = [("Nanay", 64, ["migo.santos", "tomas.santos"]), ("Lola Remy", 41, ["sofia.santos"])]
# Tiles the demo child has their family's own recording on.
DEMO_RECORDINGS = ["mama", "gusto ko"]

REJECTION_NOTES = [
    "Malabo ang screenshot at hindi mabasa ang reference number. Pakipadala ulit nang mas malinaw.",
    "Hindi tugma ang halaga: ₱100 lang ang nakita namin sa GCash. Ang SalitAACo Plus ay ₱149.",
    "Wala kaming nakitang bayad na may ganitong reference number sa aming GCash. Pakisuri at ipadala muli.",
    "Ibang GCash account ang napadalhan. Pakisuri ang numero sa Plano at Subscription.",
]

RATING_COMMENTS = {
    5: [
        "Malaking tulong kay Miguel. Nasasabi na niya kapag gutom o pagod siya.",
        "Ang ganda ng boses ng pamilya! Tuwang-tuwa ang anak ko kapag boses ni Lola ang naririnig.",
        "Madaling gamitin kahit ng lola niya. Salamat sa gumawa nito.",
        "Unang beses na nasabi ng anak ko na 'gusto ko kumain' nang hindi umiiyak. Salamat po!",
        "Sulit ang Plus. Nagagamit namin ito sa therapy at sa bahay.",
        "Gusto ko na Filipino ang mga salita. Mas naiintindihan ng anak ko.",
        "",
        "",
    ],
    4: [
        "Maganda at madaling gamitin. Sana may mas maraming board pa tungkol sa paaralan.",
        "Nakakatulong talaga. Sana mas malaki pa ang tile sa maliit na tablet.",
        "Okay na okay. Sana may English din para sa mga pinsan niya.",
        "Maayos ang app. Medyo matagal lang mag-load minsan sa mabagal na internet.",
        "",
    ],
    3: ["Maganda pero gusto ko sanang madagdagan pa ang mga pandiwa.", "Ayos lang, nag-aaral pa kami gamitin."],
    2: ["Nahirapan kaming mag-record ng boses sa cellphone."],
}

SUPPORT_MESSAGES = [
    ("Paano po ilipat ang boses ni Nanay sa isa ko pang anak? Hindi ko makita sa settings.", True),
    ("Hindi po tumutunog ang tile na 'kumain' sa tablet namin. Gumagana naman sa cellphone.", True),
    ("Nagbayad po ako kahapon sa GCash pero Free pa rin ang nakalagay. Pakisuri po.", True),
    ("Puwede po bang magdagdag ng salitang 'pasalubong'? Lagi itong hinahanap ng anak ko.", False),
    ("Nakalimutan ng anak ko ang password niya. Paano ko po ito papalitan?", True),
    ("May paraan po ba para gamitin ang app nang walang internet? Madalas mawalan ng signal sa amin.", False),
    ("Gusto ko po sanang i-print ang paggamit ng anak ko para ipakita sa therapist niya.", False),
    ("Lumalabas po na naabot ko na ang limit ng bata kahit dalawa lang sila. Plus na po ako.", True),
    ("Salamat po sa app! Tanong lang: puwede bang palitan ang larawan ng board na ginawa ko?", True),
    ("Hindi ko po ma-upload ang screenshot ng bayad, laging may error.", False),
    ("Mabagal po mag-load ang board kapag gabi. Normal lang po ba ito?", False),
]

AVATAR_COLOURS = ["#1E2F4F", "#023EBA", "#0F766E", "#9D174D", "#B45309", "#4338CA", "#047857"]


def font(size, bold=True):
    names = ["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold else ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def png_bytes(image):
    buffer = BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def initials_avatar(name, colour):
    """A plain circle-friendly square with the person's initials. No photos of people."""
    size = 256
    image = Image.new("RGB", (size, size), colour)
    draw = ImageDraw.Draw(image)
    initials = "".join(part[0] for part in name.split()[:2]).upper()
    draw.text((size / 2, size / 2), initials, fill="#FFFFFF", font=font(104), anchor="mm")
    return png_bytes(image)


def sample_qr():
    """A made-up QR-like pattern, clearly labelled SAMPLE. It does not scan to anything."""
    modules, cell, margin = 29, 14, 40
    side = modules * cell + margin * 2
    image = Image.new("RGB", (side, side + 90), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    rng = random.Random(7)

    def finder(col, row):
        x, y = margin + col * cell, margin + row * cell
        draw.rectangle([x, y, x + 7 * cell - 1, y + 7 * cell - 1], fill="#0F1E3A")
        draw.rectangle([x + cell, y + cell, x + 6 * cell - 1, y + 6 * cell - 1], fill="#FFFFFF")
        draw.rectangle([x + 2 * cell, y + 2 * cell, x + 5 * cell - 1, y + 5 * cell - 1], fill="#0F1E3A")

    reserved = lambda c, r: (c < 8 and r < 8) or (c > modules - 9 and r < 8) or (c < 8 and r > modules - 9)  # noqa: E731
    for row in range(modules):
        for col in range(modules):
            if not reserved(col, row) and rng.random() < 0.48:
                x, y = margin + col * cell, margin + row * cell
                draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill="#0F1E3A")
    finder(0, 0)
    finder(modules - 7, 0)
    finder(0, modules - 7)

    # The label across the middle, and the caption under it.
    box_w, box_h = 250, 74
    cx, cy = side / 2, margin + modules * cell / 2
    draw.rounded_rectangle([cx - box_w / 2, cy - box_h / 2, cx + box_w / 2, cy + box_h / 2], 12, fill="#FFFFFF", outline="#C2410C", width=5)
    draw.text((cx, cy), "SAMPLE", fill="#C2410C", font=font(48), anchor="mm")
    draw.text((side / 2, side + 30), "SAMPLE QR · hindi totoong GCash", fill="#C2410C", font=font(26), anchor="mm")
    return png_bytes(image)


def sample_proof(amount, reference, moment, name, number):
    """A made-up phone screenshot of a successful payment, clearly labelled SAMPLE PROOF."""
    width, height = 540, 960
    image = Image.new("RGB", (width, height), "#F3F6FB")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, width, 210], fill="#023EBA")
    draw.text((width / 2, 80), "Matagumpay ang bayad", fill="#FFFFFF", font=font(34), anchor="mm")
    draw.text((width / 2, 140), f"₱{amount:,}.00", fill="#FFFFFF", font=font(56), anchor="mm")
    draw.rounded_rectangle([36, 250, width - 36, 700], 24, fill="#FFFFFF")
    rows = [
        ("Ipinadala kay", name),
        ("Numero", number),
        ("Halaga", f"₱{amount:,}.00"),
        ("Petsa", timezone.localtime(moment).strftime("%b %d, %Y %I:%M %p")),
        ("Ref. No.", reference),
    ]
    for index, (label, value) in enumerate(rows):
        y = 300 + index * 80
        draw.text((70, y), label, fill="#64748B", font=font(24, bold=False))
        draw.text((width - 70, y), value, fill="#0F1E3A", font=font(24), anchor="ra")
    # The watermark, on its own layer so it can be turned.
    mark = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(mark).text((width / 2, height / 2), "SAMPLE PROOF", fill=(194, 65, 12, 120), font=font(76), anchor="mm")
    image = Image.alpha_composite(image.convert("RGBA"), mark.rotate(32, center=(width / 2, height / 2))).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, height - 120, width, height], fill="#FFF7ED")
    draw.text((width / 2, height - 60), "SAMPLE PROOF · para sa screenshot lang", fill="#C2410C", font=font(26), anchor="mm")
    return png_bytes(image)


def tile_words_of_boards():
    """{board: [words a child taps on it]}, a verb in its three forms."""
    words = {}
    for category in CATEGORIES:
        for item in category["items"]:
            forms = [item["verb"][aspect] for aspect in VERB_ASPECTS] if "verb" in item else [item["w"]]
            words.setdefault(category["name"], []).extend(forms)
    return words


class Command(BaseCommand):
    help = "Seed the screenshot database (screenshots.sqlite3 only) with made-up data for screenshots/capture.py."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Delete the screenshot database and its uploads first, then migrate and seed afresh.")

    # ----- Guards -----

    def check_target(self):
        database = settings.DATABASES["default"]
        if "sqlite3" not in database["ENGINE"] or Path(str(database["NAME"])).name != DATABASE_FILE:
            raise CommandError(
                f"Refusing to run: the database is {database['NAME']!s}, not {DATABASE_FILE}. "
                f"Set DB_ENGINE=sqlite and DB_NAME={DATABASE_FILE}."
            )
        media = Path(settings.MEDIA_ROOT).resolve()
        if media == (Path(settings.BASE_DIR) / "media").resolve() or not str(media).startswith(str(Path(settings.BASE_DIR).resolve())):
            raise CommandError(
                f"Refusing to run: MEDIA_ROOT is {media}. Point it at the screenshots' own folder, "
                "e.g. MEDIA_ROOT=<repo>/screenshots/_media."
            )
        return Path(str(database["NAME"])), media

    def handle(self, *args, **options):
        database_path, media = self.check_target()
        self.rng = random.Random(2026)
        self.now = timezone.now()
        self.today = timezone.localdate()

        if options["reset"]:
            connection.close()
            if database_path.exists():
                database_path.unlink()
            shutil.rmtree(media, ignore_errors=True)
            self.stdout.write(f"Deleted {database_path.name} and {media}.")
        media.mkdir(parents=True, exist_ok=True)

        call_command("migrate", verbosity=0)
        if GuardianAccount.objects.exclude(user__username__in=PLACEHOLDER_USERNAMES).exists():
            raise CommandError("The screenshot database is already seeded. Run again with --reset.")

        # The child first: a guardian cannot go while they have children.
        for username in reversed(PLACEHOLDER_USERNAMES):
            User.objects.filter(username=username).delete()
        self.password_hash = make_password(PASSWORD)

        # One transaction: SQLite on Windows is slow to commit each row on its own.
        with transaction.atomic():
            self.seed_settings_and_plans()
            self.seed_vocabulary()
            self.seed_admins()
            self.seed_guardians()
            self.seed_demo_family()
            self.seed_usage()
            self.seed_payments()
            self.seed_ratings()
            self.seed_support_messages()
            self.seed_reports()
        self.print_logins()

    # ----- Helpers -----

    def at(self, days_ago, hour=None, minute=None):
        """A moment `days_ago` days back, in Manila, never later than a few minutes ago."""
        hour = self.rng.randint(7, 21) if hour is None else hour
        minute = self.rng.randint(0, 59) if minute is None else minute
        day = self.today - timedelta(days=days_ago)
        moment = timezone.make_aware(datetime.combine(day, time(hour, minute)))
        return min(moment, self.now - timedelta(minutes=self.rng.randint(3, 40)))

    def make_user(self, username, joined, email="", active=True, last_login=None):
        return User.objects.create(
            username=username, email=email, password=self.password_hash, is_active=active,
            date_joined=joined, last_login=last_login,
        )

    def backdate(self, model, pk, **fields):
        model.objects.filter(pk=pk).update(**fields)

    def give_avatar(self, account, colour):
        account.set_avatar(random_upload_name("image/png"), ContentFile(initials_avatar(account.display_name, colour)), "image/png")

    # ----- Seeding -----

    def seed_settings_and_plans(self):
        setting = SiteSetting.load()
        setting.contact_email = "tulong@salitaaco.ph"
        setting.contact_phone = "+63 917 555 0142"
        setting.maintenance_mode = False
        setting.maintenance_message = (
            "Inaayos namin ang board para mas bumilis ito. Babalik kami bandang 10:00 ng gabi. Salamat sa pasensya!"
        )
        setting.gcash_name = "SalitAACo Payments"
        setting.gcash_number = "0917 555 0142"
        setting.free_word_limit = 0
        setting.plus_word_limit = 20
        setting.free_board_limit = 0
        setting.plus_board_limit = 5
        setting.save()
        setting.set_gcash_qr(random_upload_name("image/png"), ContentFile(sample_qr()), "image/png")

        Plan.objects.filter(key=FREE).update(child_limit=1, family_voice_limit=2)
        Plan.objects.filter(key=PLUS).update(child_limit=3, family_voice_limit=None)
        self.plus = Plan.objects.get(key=PLUS)

    def seed_vocabulary(self):
        for board, word, emoji, days_ago in ADDED_WORDS:
            added = AddedWord.objects.create(board=board, word=word, emoji=emoji)
            self.backdate(AddedWord, added.pk, created_at=self.at(days_ago), updated_at=self.at(days_ago))
        status = BoardStatus.objects.create(board=HIDDEN_BOARD, is_published=False)
        self.backdate(BoardStatus, status.pk, updated_at=self.at(HIDDEN_BOARD_DAYS_AGO, 16, 20))

    def seed_admins(self):
        self.admins = []
        for index, (username, name, joined_days, has_avatar) in enumerate(ADMINS):
            user = self.make_user(
                username, self.at(joined_days, 9), email=f"{username}@{EMAIL_DOMAIN}",
                last_login=self.at(self.rng.randint(0, 3)),
            )
            add_to_group(user, ADMINISTRATOR)
            account = AdminAccount.objects.create(user=user, display_name=name)
            if has_avatar:
                self.give_avatar(account, AVATAR_COLOURS[index])
            self.backdate(AdminAccount, account.pk, created_at=user.date_joined)
            self.admins.append(user)

    def seed_guardians(self):
        self.guardians = []  # (GuardianAccount, story)
        self.children = []   # (ChildAccount, activity from 0 to 1, first day they could tap)
        colour = iter(AVATAR_COLOURS * 4)
        for username, name, age, joined_days, story, active, has_avatar, kids in GUARDIANS:
            joined = self.at(joined_days)
            # Most come back: a later login for all but the newest.
            seen_days = 0 if joined_days == 0 else self.rng.randint(0, min(joined_days, 12 if active else 40))
            user = self.make_user(
                username, joined, email=f"{username}@{EMAIL_DOMAIN}", active=active,
                last_login=max(joined, self.at(seen_days)),
            )
            add_to_group(user, GUARDIAN)
            guardian = GuardianAccount.objects.create(
                user=user, display_name=name, age=age,
                privacy_consent_at=joined, privacy_consent_version=PRIVACY_TERMS_VERSION,
            )
            self.backdate(GuardianAccount, guardian.pk, created_at=joined)
            if has_avatar:
                self.give_avatar(guardian, next(colour))
            self.guardians.append((guardian, story))

            for kid_index, (kid_name, kid_username, kid_age) in enumerate(kids):
                kid_joined_days = max(0, joined_days - kid_index * self.rng.randint(0, 4) - (1 if joined_days > 1 else 0))
                kid_joined = max(joined + timedelta(minutes=10), self.at(kid_joined_days))
                kid_joined = min(kid_joined, self.now - timedelta(minutes=2))
                activity = self.rng.uniform(0.35, 0.95) if active else self.rng.uniform(0.15, 0.4)
                kid_seen = 0 if activity > 0.6 else self.rng.randint(0, 6)
                kid_user = self.make_user(
                    kid_username, kid_joined, last_login=max(kid_joined, self.at(min(kid_seen, kid_joined_days))),
                )
                add_to_group(kid_user, CHILD)
                child = ChildAccount.objects.create(user=kid_user, display_name=kid_name, age=kid_age, guardian=guardian)
                self.backdate(ChildAccount, child.pk, created_at=kid_joined)
                self.children.append((child, activity, kid_joined_days))

        self.demo_guardian = self.guardians[0][0]
        demo_kids = {child.user.username: child for child, _, _ in self.children if child.guardian_id == self.demo_guardian.pk}
        self.demo_children = demo_kids
        self.demo_child = demo_kids["migo.santos"]
        # The demo family is active every day; the demo child has a picture, as does one more child.
        self.children = [
            (child, 0.97 if child.guardian_id == self.demo_guardian.pk else activity, first)
            for child, activity, first in self.children
        ]
        self.give_avatar(self.demo_child, "#023EBA")
        self.give_avatar(demo_kids["tomas.santos"], "#0F766E")
        User.objects.filter(pk__in=[c.user_id for c in demo_kids.values()]).update(last_login=self.at(0, 8, 5))

    def seed_demo_family(self):
        guardian = self.demo_guardian
        self.demo_own_words = []
        for name, emoji, days_ago, words in DEMO_BOARDS:
            board = GuardianBoard.objects.create(guardian=guardian, name=name, emoji=emoji)
            self.backdate(GuardianBoard, board.pk, created_at=self.at(days_ago, 20))
            for offset, (word, word_emoji) in enumerate(words):
                tile = GuardianWord.objects.create(guardian=guardian, board=name, word=word, emoji=word_emoji)
                self.backdate(GuardianWord, tile.pk, created_at=self.at(days_ago, 20, 10 + offset))
                self.demo_own_words.append((name, word))
        for board, word, emoji, days_ago in DEMO_APP_BOARD_WORDS:
            tile = GuardianWord.objects.create(guardian=guardian, board=board, word=word, emoji=emoji)
            self.backdate(GuardianWord, tile.pk, created_at=self.at(days_ago, 21))
            self.demo_own_words.append((board, word))

        for username, board in DEMO_HIDDEN_BOARDS:
            HiddenBoard.objects.create(child=self.demo_children[username], board=board)

        # The family's tiles in the shared voice, as ElevenLabs would have made them.
        shared = tile_audio_directory()
        fallback = shared / tile_audio_file_name(PREVIEW_WORD)
        for tile in guardian.words.all():
            path = guardian_word_audio_path(tile)
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fallback, path)

        # The family voices, every word already made: copies of the shared voice's files,
        # so that the page shows them finished and never asks ElevenLabs for more.
        for index, (name, days_ago, listeners) in enumerate(DEMO_VOICES):
            voice = FamilyVoice.objects.create(
                guardian=guardian, name=name, elevenlabs_voice_id=f"sample-voice-{index + 1:02d}-not-real",
                consent_at=self.at(days_ago, 19), consent_version=TERMS_VERSION,
            )
            self.backdate(FamilyVoice, voice.pk, created_at=self.at(days_ago, 19, 30))
            directory = family_voice_directory(voice)
            directory.mkdir(parents=True, exist_ok=True)
            for word in family_voice_words(voice):
                source = shared / tile_audio_file_name(word)
                shutil.copyfile(source if source.exists() else fallback, directory / tile_audio_file_name(word))
            ChildAccount.objects.filter(user__username__in=listeners).update(family_voice=voice)

        # The demo child's own recordings on two tiles.
        for word in DEMO_RECORDINGS:
            customization = Customization(user=self.demo_child.user, word=word)
            audio = (shared / tile_audio_file_name(word)).read_bytes()
            customization.set_sound(random_upload_name("audio/mpeg"), ContentFile(audio), "audio/mpeg")

    def seed_usage(self):
        board_words = tile_words_of_boards()
        for board, word, _, _ in ADDED_WORDS:
            board_words[board].append(word)
        demo_extra = {}
        for board, word in self.demo_own_words:
            demo_extra.setdefault(board, []).append(word)
        # The family taps their own tiles (names, their dog) often.
        own_words = {word for _, word in self.demo_own_words}

        daily, totals = [], {}
        for child, activity, first_day in self.children:
            hidden = set(child.hidden_boards.values_list("board", flat=True))
            boards = {name: list(words) for name, words in board_words.items() if name not in hidden}
            if child.guardian_id == self.demo_guardian.pk:
                for name, words in demo_extra.items():
                    if name not in hidden:
                        boards.setdefault(name, []).extend(words)
            taste = {word: self.rng.uniform(0.5, 1.6) for words in boards.values() for word in words}

            def choices(include_hidden_board):
                """The words and boards the child could tap and open, with how much they like each."""
                shown = {name: words for name, words in boards.items() if include_hidden_board or name != HIDDEN_BOARD}
                words = [word for name_words in shown.values() for word in name_words]
                weights = [POPULAR_WORDS.get(word, 1) * taste[word] * (3 if word in own_words else 1) for word in words]
                names = list(shown)
                return words, weights, names, [BOARD_WEIGHTS.get(name, 4) for name in names]

            before_hiding, after_hiding = choices(True), choices(False)

            for days_ago in range(min(first_day, DAYS - 1), -1, -1):
                words, weights, board_names, board_weights = (
                    before_hiding if days_ago > HIDDEN_BOARD_DAYS_AGO else after_hiding
                )
                # Weekends a little busier; the board took a few days to get used to.
                weekday = (self.today - timedelta(days=days_ago)).weekday()
                chance = activity * (1.1 if weekday >= 5 else 1.0)
                if self.rng.random() > chance:
                    continue
                day = self.today - timedelta(days=days_ago)
                taps = int(self.rng.randint(6, 34) * (0.6 + activity))
                counts = {}
                for word in self.rng.choices(words, weights, k=taps):
                    counts[word] = counts.get(word, 0) + 1
                for word, count in counts.items():
                    daily.append(DailyUsage(user=child.user, day=day, kind=DailyUsage.WORD, name=word, use_count=count))
                    totals[(child.user_id, word)] = totals.get((child.user_id, word), 0) + count
                opens = {}
                for board in self.rng.choices(board_names, board_weights, k=self.rng.randint(2, 7)):
                    opens[board] = opens.get(board, 0) + 1
                for board, count in opens.items():
                    daily.append(DailyUsage(user=child.user, day=day, kind=DailyUsage.BOARD, name=board, use_count=count))

        DailyUsage.objects.bulk_create(daily, batch_size=2000)
        WordUsage.objects.bulk_create(
            [WordUsage(user_id=user_id, word=word, use_count=count) for (user_id, word), count in totals.items()],
            batch_size=2000,
        )
        self.stdout.write(f"Usage: {len(daily)} daily rows, {len(totals)} word totals.")

    def add_payment(self, guardian, status, created, reviewer=None, reviewed=None, starts=None, note=""):
        reference = f"{self.rng.randint(1000, 9999)} {self.rng.randint(100, 999)} {self.rng.randint(100000, 999999)}"
        proof = sample_proof(self.plus.price, reference, created, "SalitAACo Payments", "0917 555 0142")
        payment = Payment(guardian=guardian, plan=self.plus, amount=self.plus.price, status=status, note=note,
                          proof_mime="image/png")
        payment.proof.save(random_upload_name("image/png"), ContentFile(proof), save=False)
        if status != PENDING:
            payment.reviewed_at = reviewed
            payment.reviewed_by = reviewer
        if status == APPROVED:
            payment.starts_at = starts
            payment.ends_at = add_months(starts, 1)
        payment.save()
        self.backdate(Payment, payment.pk, created_at=created)
        return payment

    def approve_chain(self, guardian, first_days_ago, until_now=True, count=None):
        """Monthly approved payments from `first_days_ago`: up to now (on Plus), or `count` of them."""
        paid_until = None
        made = 0
        days_ago = first_days_ago
        while True:
            created = self.at(days_ago)
            reviewed = min(created + timedelta(hours=self.rng.randint(1, 20)), self.now - timedelta(minutes=5))
            starts = max(reviewed, paid_until or reviewed)
            payment = self.add_payment(guardian, APPROVED, created, self.rng.choice(self.admins), reviewed, starts)
            paid_until = payment.ends_at
            made += 1
            if count is not None and made >= count:
                return
            if until_now and paid_until > self.now:
                return
            # The next one is paid a few days before the month runs out.
            renew = timezone.localtime(paid_until).date() - timedelta(days=self.rng.randint(1, 4))
            days_ago = max(0, (self.today - renew).days)

    def seed_payments(self):
        notes = iter(REJECTION_NOTES * 3)
        for guardian, story in self.guardians:
            joined_days = (self.today - timezone.localtime(guardian.user.date_joined).date()).days
            if guardian.pk == self.demo_guardian.pk:
                # A blurry first try, then three months of Plus, paid a little early each time.
                created = self.at(joined_days - 2, 20)
                self.add_payment(guardian, REJECTED, created, self.admins[0], created + timedelta(hours=3), note=next(notes))
                self.approve_chain(guardian, joined_days - 3)
            elif story == "plus":
                if self.rng.random() < 0.25:
                    created = self.at(max(0, joined_days - 1))
                    self.add_payment(guardian, REJECTED, created, self.rng.choice(self.admins),
                                     created + timedelta(hours=5), note=next(notes))
                self.approve_chain(guardian, max(0, joined_days - self.rng.randint(1, 6)))
            elif story == "lapsed":
                # Paid once or twice, long enough ago that the months have run out.
                months = 2 if joined_days > 70 else 1
                self.approve_chain(guardian, joined_days - 1, until_now=False, count=months)
            elif story == "pending":
                created = self.at(self.rng.randint(0, min(5, joined_days)))
                if joined_days > 30:
                    old = self.at(joined_days - 5)
                    self.add_payment(guardian, REJECTED, old, self.rng.choice(self.admins), old + timedelta(hours=6),
                                     note=next(notes))
                self.add_payment(guardian, PENDING, created)
            elif story == "rejected":
                for days_ago in (joined_days - 2, max(0, joined_days - 9)):
                    created = self.at(days_ago)
                    self.add_payment(guardian, REJECTED, created, self.rng.choice(self.admins),
                                     created + timedelta(hours=8), note=next(notes))
        self.stdout.write(f"Payments: {Payment.objects.count()} "
                          f"({Payment.objects.filter(status=PENDING).count()} waiting).")

    def seed_ratings(self):
        raters = [guardian.user for guardian, _ in self.guardians if guardian.user.is_active][:18]
        raters += [child.user for child, activity, _ in self.children if activity > 0.5][:14]
        star_choices = [5] * 14 + [4] * 9 + [3] * 2 + [2]
        for user in raters:
            joined_days = (self.today - timezone.localtime(user.date_joined).date()).days
            stars = self.rng.choice(star_choices)
            # A child's rating is short or has no comment.
            comment = self.rng.choice(RATING_COMMENTS[stars]) if hasattr(user, "guardian_account") else ""
            if user.username == "maricel.santos":
                stars, comment = 5, RATING_COMMENTS[5][0]
            rating = Rating.objects.create(user=user, rating=stars, comment=comment or None)
            moment = self.at(self.rng.randint(0, max(0, joined_days - 1)))
            self.backdate(Rating, rating.pk, created_at=moment, updated_at=moment)

    def seed_support_messages(self):
        writers = [guardian for guardian, _ in self.guardians if guardian.user.is_active]
        for index, (text, resolved) in enumerate(SUPPORT_MESSAGES):
            guardian = self.demo_guardian if index in (0, 6) else writers[(index * 3) % len(writers)]
            child = guardian.children.order_by("display_name").first() if index % 2 == 0 else None
            joined_days = (self.today - timezone.localtime(guardian.user.date_joined).date()).days
            created = self.at(self.rng.randint(0, max(0, min(joined_days - 1, 45))) if index > 2 else index)
            message = SupportMessage.objects.create(guardian=guardian, child=child, message=text)
            fields = {"created_at": created}
            if resolved:
                fields["resolved_at"] = min(created + timedelta(hours=self.rng.randint(2, 30)), self.now - timedelta(minutes=1))
            self.backdate(SupportMessage, message.pk, **fields)

    def seed_reports(self):
        # Made by the app's own report code, so the files are what Mga Ulat makes.
        from salitaaco.forms.generated_reports.feedback_report import FeedbackReportForm
        from salitaaco.forms.generated_reports.payments_report import PaymentsReportForm
        from salitaaco.forms.generated_reports.users_report import UsersReportForm
        from salitaaco.routes.generated_reports.generated_reports import make_report

        start = (self.today - timedelta(days=DAYS - 1)).isoformat()
        month_start = (self.today - timedelta(days=29)).isoformat()
        end = self.today.isoformat()
        plans = [
            (FEEDBACK, FeedbackReportForm, CSV, start, {
                "rating_columns": [value for value, _ in RATING_COLUMNS],
                "message_columns": [value for value, _ in MESSAGE_COLUMNS],
            }),
            (PAYMENTS, PaymentsReportForm, PRINTABLE, start, {"columns": [value for value, _ in PAYMENT_COLUMNS]}),
            (USERS, UsersReportForm, PRINTABLE, month_start, {"columns": [value for value, _ in USER_COLUMNS]}),
        ]
        for report_type, form_class, file_type, first, columns in plans:
            data = {f"{report_type}-file_type": file_type, f"{report_type}-start_date": first, f"{report_type}-end_date": end}
            data.update({f"{report_type}-{name}": value for name, value in columns.items()})
            form = form_class(data, prefix=report_type)
            if not form.is_valid():
                raise CommandError(f"The {report_type} report form refused the seed: {form.errors.as_text()}")
            make_report(report_type, form, self.admins[0])

    def print_logins(self):
        self.stdout.write(self.style.SUCCESS("\nSeeded. Every account's password: " + PASSWORD))
        self.stdout.write(f"  Admin     {ADMINS[0][0]}")
        self.stdout.write(f"  Guardian  {GUARDIANS[0][0]}  (SalitAACo Plus, 3 children)")
        self.stdout.write(f"  Child     {self.demo_child.user.username}  ({self.demo_child.display_name})")
        self.stdout.write("  Free guardian with a waiting payment: cristina.lopez")
