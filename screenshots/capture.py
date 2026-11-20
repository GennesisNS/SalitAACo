"""
Screenshots of every SalitAACo page, at desktop size, from a fresh made-up seed.

    .venv\\Scripts\\python.exe screenshots\\capture.py

It reseeds the screenshot database (screenshots.sqlite3, never db.sqlite3)
with `manage.py seed_screenshots --reset`, starts the app on a free port with
its own uploads folder (screenshots/_media) and no ElevenLabs key, logs in
through /login/ as each role, saves a PNG of every page and of every state a
button opens, writes screenshots/README.md as the index, and stops the server.

Options:
    --only public,auth,child,guardian,admin,maintenance   capture only these sides
    --no-seed                                              reuse the current screenshot database
"""
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
SHOTS = REPO / "screenshots"
MEDIA = SHOTS / "_media"
PYTHON = sys.executable
PASSWORD = "Salita#2026"
VIEWPORT = {"width": 1920, "height": 1080}

ADMIN = "andrea.villanueva"
GUARDIAN = "maricel.santos"
SECOND_GUARDIAN = "joel.dizon"   # On Plus with 2 of 3 children: the add-a-child window is open to him.
CHILD = "migo.santos"

SIDES = ["public", "auth", "child", "guardian", "admin", "maintenance"]
SIDE_FOLDERS = {
    "public": "01-public",
    "auth": "02-auth",
    "child": "03-child",
    "guardian": "04-guardian",
    "admin": "05-admin",
    "maintenance": "06-maintenance",
}

# What the board sends while it is used. Blocked during the capture so that
# looking around the board does not add to the seeded counts.
COUNTING_URLS = ["**/dashboard/board/usage/increment/", "**/dashboard/board/usage/board/"]


def app_env():
    env = os.environ.copy()
    env.update({
        "DB_ENGINE": "sqlite",
        "DB_NAME": "screenshots.sqlite3",
        "MEDIA_ROOT": str(MEDIA),
        "DJANGO_DEBUG": "True",
        "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1",
        "ELEVENLABS_API_KEY": "",
        "ELEVENLABS_VOICE_ID": "",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    })
    return env


def manage(*args, capture=False):
    result = subprocess.run(
        [PYTHON, "manage.py", *args], cwd=REPO, env=app_env(), check=True,
        capture_output=capture, text=True, encoding="utf-8",
    )
    return result.stdout if capture else None


def django_shell(code):
    return manage("shell", "-c", code, capture=True)


def check_environment():
    """Stop unless the app would use the screenshot database, its own uploads and no ElevenLabs key."""
    out = django_shell(
        "import json; from django.conf import settings as s; "
        "print(json.dumps({'db': str(s.DATABASES['default']['NAME']), 'media': str(s.MEDIA_ROOT), "
        "'key': s.ELEVENLABS_API_KEY}))"
    )
    found = json.loads(out.strip().splitlines()[-1])
    if Path(found["db"]).name != "screenshots.sqlite3" or Path(found["media"]).resolve() != MEDIA.resolve() or found["key"]:
        sys.exit(f"Refusing to capture: the app would use {found['db']}, {found['media']}, "
                 f"and an ElevenLabs key is {'set' if found['key'] else 'not set'}.")


def seeded_ids():
    out = django_shell(
        "import json\n"
        "from salitaaco.models.child_account import ChildAccount\n"
        "from salitaaco.models.generated_report import GeneratedReport\n"
        "kids = {c.user.username: str(c.uuid) for c in ChildAccount.objects.select_related('user')}\n"
        "reports = {r.report_type: str(r.uuid) for r in GeneratedReport.objects.filter(file_type='printable')}\n"
        "print(json.dumps({'kids': kids, 'reports': reports}))"
    )
    return json.loads(out.strip().splitlines()[-1])


def set_maintenance(on):
    django_shell(
        "from salitaaco.models.site_setting import SiteSetting\n"
        f"SiteSetting.objects.filter(pk=SiteSetting.ONLY_ROW).update(maintenance_mode={bool(on)})"
    )


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_server(port):
    log = open(SHOTS / "_media" / "server.log", "w", encoding="utf-8")
    server = subprocess.Popen(
        [PYTHON, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=REPO, env=app_env(), stdout=log, stderr=subprocess.STDOUT,
    )
    deadline = time.time() + 60
    while time.time() < deadline:
        if server.poll() is not None:
            sys.exit("The server stopped while starting; see screenshots/_media/server.log.")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return server
        except OSError:
            time.sleep(0.5)
    server.kill()
    sys.exit("The server did not start within a minute.")


class Shooter:
    """Saves numbered PNGs into one folder and remembers them for the index."""

    def __init__(self, base, index, side):
        self.base = base
        self.index = index
        self.side = side
        self.counters = {}

    def folder(self, folder):
        path = SHOTS / SIDE_FOLDERS[self.side] / folder if folder else SHOTS / SIDE_FOLDERS[self.side]
        if path not in self.counters:
            if path.exists():
                for old in path.glob("*.png"):
                    old.unlink()
            path.mkdir(parents=True, exist_ok=True)
            self.counters[path] = 0
        return path

    def settle(self, page, keep_toast=False):
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeout:
            pass
        page.evaluate("() => document.fonts.ready.then(() => true)")
        page.evaluate("""() => Promise.all(Array.from(document.images)
            .filter((img) => !img.complete)
            .map((img) => new Promise((done) => { img.onload = img.onerror = done; })))""")
        if not keep_toast:
            # What the toast's own ✕ does.
            page.evaluate("() => document.querySelectorAll('.toast').forEach((toast) => toast.remove())")
        # No focus ring left on the last button clicked.
        page.evaluate("() => document.activeElement && document.activeElement.blur && document.activeElement.blur()")
        page.wait_for_timeout(250)

    def shot(self, page, folder, name, page_name, role, what, full=True, keep_toast=False):
        self.settle(page, keep_toast)
        path = self.folder(folder)
        self.counters[path] += 1
        file = path / f"{self.counters[path]:02d}-{name}.png"
        page.screenshot(path=file, animations="disabled", caret="hide")
        files = [file]
        if full:
            height = page.evaluate("() => Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)")
            if height > VIEWPORT["height"] + 8:
                full_file = file.with_name(f"{file.stem}-full.png")
                page.screenshot(path=full_file, animations="disabled", caret="hide", full_page=True)
                files.append(full_file)
        url = page.url.replace(self.base, "") or "/"
        for item in files:
            self.index.append({
                "file": item.relative_to(SHOTS).as_posix(),
                "page": page_name,
                "url": url,
                "role": role,
                "what": what + (" (whole page)" if item.stem.endswith("-full") else ""),
            })
        print(f"  {files[0].relative_to(SHOTS).as_posix()}{'  +full' if len(files) > 1 else ''}")


# ----- Helpers for the browser -----

def new_page(browser, block_counting=False):
    context = browser.new_context(
        viewport=VIEWPORT, device_scale_factor=1, color_scheme="light",
        locale="fil-PH", timezone_id="Asia/Manila",
    )
    page = context.new_page()
    if block_counting:
        for pattern in COUNTING_URLS:
            page.route(pattern, lambda route: route.fulfill(status=200, content_type="application/json", body='{"ok": true}'))
    return page


def login(page, base, username):
    page.goto(f"{base}/login/")
    page.fill("#id_username", username)
    page.fill("#id_password", PASSWORD)
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    if "/login/" in page.url:
        sys.exit(f"Could not log in as {username}.")


def go(page, url):
    page.goto(url)
    page.wait_for_load_state("networkidle")


def open_modal(page, selector):
    button = page.locator(selector).first
    name = button.get_attribute("data-open-modal")
    button.scroll_into_view_if_needed()
    button.click()
    page.wait_for_selector(f'[data-modal="{name}"]:not(.hidden)')


def board_screen(page, fragment):
    page.evaluate(f"() => {{ location.hash = {json.dumps(fragment)}; }}")
    page.wait_for_timeout(400)
    page.evaluate("() => window.scrollTo(0, 0)")


def tap(page, word):
    page.locator("#grid .cell, #feelingsGrid .cell").filter(has_text=word).first.click()


# ----- The sides -----

def capture_public(page, base, s):
    role = "Logged out"
    go(page, f"{base}/")
    s.shot(page, "", "landing-hero", "Public website", role, "The hero and the tile demo, as the page opens")
    for anchor, name, what in [
        ("features", "features", "“Ano ang nagagawa ng SalitAACo”"),
        ("about", "about-us", "Tungkol sa Amin"),
        ("plans", "plans", "Mga Plano, from the plan rows"),
    ]:
        page.locator(f"#{anchor}").scroll_into_view_if_needed()
        page.evaluate(f"() => document.getElementById('{anchor}').scrollIntoView({{block: 'start'}})")
        s.shot(page, "", name, "Public website", role, what + (", with the footer" if anchor == "plans" else ""), full=False)
    go(page, f"{base}/")
    for word in ["gusto ko", "kumain"]:
        tiles = page.locator("#demoGrid button, #demoGrid .cell, #demoGrid > *").filter(has_text=word)
        if tiles.count():
            tiles.first.click()
    s.shot(page, "", "landing-demo-sentence", "Public website", role, "The hero's tile demo after tapping two tiles", full=False)


def capture_auth(page, base, s):
    role = "Logged out"
    go(page, f"{base}/login/")
    s.shot(page, "", "login", "Log in", role, "The login form")
    page.fill("#id_username", GUARDIAN)
    page.fill("#id_password", "mali-ang-password")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    s.shot(page, "", "login-wrong-password", "Log in", role, "The message for a wrong password")
    go(page, f"{base}/register/")
    s.shot(page, "", "register", "Sign up", role, "The guardian sign-up form")
    open_modal(page, '[data-open-modal="privacy-terms"]')
    s.shot(page, "", "register-privacy-terms", "Sign up", role, "Paalala sa Privacy, opened from the form", full=False)
    go(page, f"{base}/register/")
    page.locator("form button[type=submit]").last.click()
    page.wait_for_load_state("networkidle")
    s.shot(page, "", "register-errors", "Sign up", role, "The messages for an empty form")


def capture_child(page, base, s):
    role = f"Child ({CHILD})"
    login(page, base, CHILD)
    go(page, f"{base}/dashboard/board/#home")
    board_screen(page, "home")
    s.shot(page, "01-board-home", "home", "Board: Home", role, "Mabilis na Salita and Ang Nararamdaman Ko")
    for word in ["gusto ko", "gutom"]:
        tap(page, word)
    s.shot(page, "01-board-home", "home-sentence", "Board: Home", role, "A sentence built from two tiles")
    page.click("#clearBtn")
    page.click("#editModeBtn")
    s.shot(page, "01-board-home", "home-edit-mode", "Board: Home", role, "Edit mode: 🎙️ on each tile, ↺ on recorded ones")
    page.click("#editModeBtn")

    board_screen(page, "boards")
    s.shot(page, "02-board-mga-board", "mga-board", "Board: Mga Board", role, "Every board the child sees, the family's own included")

    for fragment, name, what in [
        ("boards/Pagkain", "pagkain", "The Pagkain board, with an admin's added words at the end"),
        ("boards/Pandiwa", "pandiwa", "The verbs board, with nangyari na / ngayon / mamaya"),
        ("boards/Pamilya Namin", "custom-pamilya-namin", "The family's own board"),
    ]:
        board_screen(page, fragment)
        s.shot(page, "03-board-single-board", name, "Board: one board", role, what)
    board_screen(page, "boards/Pandiwa")
    page.click('#aspectBar button[data-a="future"]')
    s.shot(page, "03-board-single-board", "pandiwa-mamaya", "Board: one board", role, "The verbs in their future form (mamaya)")
    board_screen(page, "boards/Pagkain")
    page.click("#editModeBtn")
    s.shot(page, "03-board-single-board", "pagkain-edit-mode", "Board: one board", role, "Edit mode on a board")
    page.click("#editModeBtn")

    board_screen(page, "favorites")
    page.wait_for_selector("#grid .cell")
    s.shot(page, "04-paborito", "paborito", "Board: Paborito", role, "The child's most-used words, most used first")

    go(page, f"{base}/dashboard/profile/")
    s.shot(page, "05-profile", "profile", "Profile", role, "The child's profile: name, age, picture, password")
    if page.locator('[data-open-modal="delete-account"]').count():
        open_modal(page, '[data-open-modal="delete-account"]')
        s.shot(page, "05-profile", "delete-account-confirm", "Profile", role, "Delete-account confirmation (not confirmed)", full=False)

    go(page, f"{base}/dashboard/settings/")
    s.shot(page, "06-settings", "settings", "Settings", role, "Tile editing, theme, tile size and the child's voice")

    go(page, f"{base}/dashboard/board/#home")
    board_screen(page, "home")
    open_modal(page, '[data-open-modal="rating"]')
    s.shot(page, "07-rating", "rating-modal", "Board: rate the app", role, "I-rate ang SalitAACo: stars and a comment", full=False)


def capture_guardian(browser, base, s, ids):
    role = f"Guardian ({GUARDIAN})"
    page = new_page(browser, block_counting=True)
    login(page, base, GUARDIAN)
    migo, sofia = ids["kids"][CHILD], ids["kids"]["sofia.santos"]
    d = f"{base}/dashboard"

    go(page, f"{d}/overview/")
    s.shot(page, "01-dashboard-buod", "buod", "Buod", role, "The children as a table, and the plan")

    go(page, f"{d}/children/")
    s.shot(page, "02-mga-bata", "mga-bata", "Mga Bata", role, "Three children: the limit of SalitAACo Plus, so adding is closed")

    second = new_page(browser)
    login(second, base, SECOND_GUARDIAN)
    go(second, f"{d}/children/")
    s.shot(second, "02-mga-bata", "mga-bata-room-for-more", "Mga Bata", f"Guardian ({SECOND_GUARDIAN})", "A guardian with room for one more child")
    open_modal(second, '[data-open-modal="create-child"]')
    s.shot(second, "02-mga-bata", "add-child-modal", "Mga Bata", f"Guardian ({SECOND_GUARDIAN})", "＋ Magdagdag ng bata", full=False)
    second.context.close()

    go(page, f"{d}/children/{migo}/")
    s.shot(page, "03-child-details", "child-details", "A child's page", role, "Name, age, picture, tiles, password")
    open_modal(page, '[data-open-modal="delete-child"]')
    s.shot(page, "03-child-details", "delete-child-confirm", "A child's page", role, "Delete-child confirmation (not confirmed)", full=False)

    go(page, f"{d}/children/{migo}/board/")
    board_screen(page, "home")
    s.shot(page, "04-child-board-setup", "child-board-home", "The child's board, for the guardian", role, "Opens in edit mode; taps here are not counted")
    board_screen(page, "boards")
    s.shot(page, "04-child-board-setup", "child-board-mga-board", "The child's board, for the guardian", role, "The boards the child sees")
    board_screen(page, "boards/Pamilya Namin")
    s.shot(page, "04-child-board-setup", "child-board-custom-board", "The child's board, for the guardian", role, "The family's own board, in edit mode")

    go(page, f"{d}/children/{migo}/boards/")
    s.shot(page, "05-napiling-bata-mga-board", "mga-board", "Napiling Bata › Mga Board", role, "Which boards Miguel sees, and the family's own boards")
    open_modal(page, '[data-open-modal="new-board"]')
    s.shot(page, "05-napiling-bata-mga-board", "add-board-modal", "Napiling Bata › Mga Board", role, "＋ Magdagdag ng board", full=False)
    go(page, f"{d}/children/{migo}/boards/")
    open_modal(page, '[data-open-modal^="edit-board-"]')
    s.shot(page, "05-napiling-bata-mga-board", "edit-board-modal", "Napiling Bata › Mga Board", role, "I-edit on a custom board", full=False)
    go(page, f"{d}/children/{migo}/boards/")
    open_modal(page, '[data-open-modal^="delete-board-"]')
    s.shot(page, "05-napiling-bata-mga-board", "delete-board-confirm", "Napiling Bata › Mga Board", role, "Delete-board confirmation (not confirmed)", full=False)
    go(page, f"{d}/children/{migo}/boards/")
    picker = page.locator("#childPicker")
    picker.select_option(label="Sofia Santos")
    page.wait_for_url(f"**/children/{sofia}/boards/")
    s.shot(page, "05-napiling-bata-mga-board", "child-picker-sofia", "Napiling Bata › Mga Board", role, "The child picker switched to Sofia: two of her boards are off")
    page.locator("#childPicker").select_option(label="Miguel Santos")
    page.wait_for_url(f"**/children/{migo}/boards/")

    go(page, f"{d}/children/{migo}/voice/")
    s.shot(page, "06-napiling-bata-boses", "boses", "Napiling Bata › Boses", role, "Which voice Miguel hears: Nanay")

    for value, name, what in [("7", "last-7-days", "Huling 7 araw"), ("30", "last-30-days", "Huling 30 araw"), ("all", "all-time", "Lahat")]:
        go(page, f"{d}/children/{migo}/usage/?range={value}")
        s.shot(page, "07-napiling-bata-paggamit", name, "Napiling Bata › Paggamit", role, f"Words and boards used: {what}")

    go(page, f"{d}/family-voices/")
    s.shot(page, "08-boses-ng-pamilya", "boses-ng-pamilya", "Boses ng Pamilya", role, "Nanay and Lola Remy, every word made")
    open_modal(page, '[data-open-modal^="delete-voice-"]')
    s.shot(page, "08-boses-ng-pamilya", "delete-voice-confirm", "Boses ng Pamilya", role, "Delete-voice confirmation (not confirmed)", full=False)

    go(page, f"{d}/tiles/")
    s.shot(page, "09-sariling-tile", "sariling-tile", "Sariling Tile", role, "The family's own tiles and the form to add one")
    open_modal(page, '[data-open-modal^="edit-word-"]')
    s.shot(page, "09-sariling-tile", "edit-tile-modal", "Sariling Tile", role, "I-edit on a tile", full=False)
    go(page, f"{d}/tiles/")
    open_modal(page, '[data-open-modal^="delete-word-"]')
    s.shot(page, "09-sariling-tile", "delete-tile-confirm", "Sariling Tile", role, "Delete-tile confirmation (not confirmed)", full=False)

    go(page, f"{d}/board/#home")
    board_screen(page, "home")
    s.shot(page, "10-mga-tile", "own-board-home", "Mga Tile (the guardian's own board)", role, "The guardian's own board")
    board_screen(page, "boards")
    s.shot(page, "10-mga-tile", "own-board-mga-board", "Mga Tile (the guardian's own board)", role, "Every board, the family's own included")
    board_screen(page, "home")
    page.click("#editModeBtn")
    s.shot(page, "10-mga-tile", "own-board-edit-mode", "Mga Tile (the guardian's own board)", role, "Edit mode")
    page.click("#editModeBtn")

    go(page, f"{d}/plan/")
    s.shot(page, "11-subscription-plano", "plano", "Plano at Subscription", role, "The plans, on SalitAACo Plus with the paid date")
    open_modal(page, '[data-open-modal="pay"]')
    s.shot(page, "11-subscription-plano", "pay-modal", "Plano at Subscription", role, "Paying by GCash: the SAMPLE QR code and the proof upload", full=False)

    go(page, f"{d}/plan/transactions/")
    s.shot(page, "12-subscription-transactions", "transactions", "Kasaysayan ng bayad", role, "Approved and rejected payments, with the reason")
    open_modal(page, '[data-open-modal="proof"]')
    page.wait_for_timeout(500)
    s.shot(page, "12-subscription-transactions", "proof-viewer", "Kasaysayan ng bayad", role, "A proof of payment (SAMPLE PROOF)", full=False)

    go(page, f"{d}/support/")
    s.shot(page, "13-tulong-at-suporta", "tulong-at-suporta", "Tulong at Suporta", role, "Guides, and the form to write to support")

    go(page, f"{d}/settings/")
    s.shot(page, "14-hitsura-at-tile", "hitsura-at-tile", "Hitsura at Tile", role, "Tile editing, theme and tile size")

    go(page, f"{d}/profile/")
    s.shot(page, "15-account", "account", "Account", role, "Name, picture, age, password")
    open_modal(page, '[data-open-modal="delete-account"]')
    s.shot(page, "15-account", "delete-account-confirm", "Account", role, "Delete-account confirmation (not confirmed)", full=False)
    page.context.close()


def capture_admin(browser, base, s, ids):
    role = f"Admin ({ADMIN})"
    page = new_page(browser, block_counting=True)
    login(page, base, ADMIN)
    d = f"{base}/dashboard"

    go(page, f"{d}/analytics/")
    s.shot(page, "01-dashboard", "dashboard", "Dashboard", role, "Taps per day, boards opened most, recent activity")

    for tab, name, what in [
        ("growth", "paglago-ng-user", "Paglago ng user"),
        ("usage", "paggamit", "Paggamit: top words and boards"),
        ("retention", "pagbabalik", "Pagbabalik"),
        ("business", "negosyo", "Negosyo: plans, revenue by month, payments by status"),
    ]:
        go(page, f"{d}/reports/?tab={tab}")
        s.shot(page, "02-analytics-at-ulat", name, "Analytics at Ulat", role, what)

    go(page, f"{d}/generated-reports/")
    s.shot(page, "03-mga-ulat", "mga-ulat", "Mga Ulat", role, "Three reports made by the app's own report code")
    for kind, name in [("users", "mga-user"), ("payments", "mga-bayad"), ("feedback", "feedback")]:
        go(page, f"{d}/generated-reports/")
        open_modal(page, '[data-open-modal="new-report"]')
        page.click(f"#reportType-{kind}")
        s.shot(page, "03-mga-ulat", f"make-report-{name}", "Mga Ulat", role, f"＋ Gumawa ng ulat: {name.replace('-', ' ')}", full=False)
    go(page, f"{d}/generated-reports/")
    open_modal(page, '[data-open-modal^="delete-report-"]')
    s.shot(page, "03-mga-ulat", "delete-report-confirm", "Mga Ulat", role, "Delete-report confirmation (not confirmed)", full=False)
    for kind, name in [("users", "printable-users-report"), ("payments", "printable-payments-report")]:
        go(page, f"{d}/generated-reports/{ids['reports'][kind]}/")
        s.shot(page, "03-mga-ulat", name, "Mga Ulat › printable report", role, "The page to print or save as PDF")

    for status, name, what in [("", "lahat", "Lahat"), ("active", "aktibo", "Aktibo"), ("inactive", "hindi-aktibo", "Hindi aktibo")]:
        go(page, f"{d}/users/?status={status}")
        s.shot(page, "04-mga-user", name, "Mga User", role, f"Accounts: {what}")
    go(page, f"{d}/users/?status=&query=santos")
    s.shot(page, "04-mga-user", "search-santos", "Mga User", role, "Searching for “santos”")
    go(page, f"{d}/users/")
    open_modal(page, '[data-open-modal^="deactivate-"]')
    s.shot(page, "04-mga-user", "deactivate-confirm", "Mga User", role, "Make-inactive confirmation (not confirmed)", full=False)

    go(page, f"{d}/vocabulary/boards/")
    s.shot(page, "05-mga-board", "mga-board", "Mga Board", role, "Published boards, and Lugar hidden from everyone")
    open_modal(page, '[data-open-modal^="hide-board-"]:not([disabled])')
    s.shot(page, "05-mga-board", "hide-board-confirm", "Mga Board", role, "Hide-board confirmation (not confirmed)", full=False)

    go(page, f"{d}/vocabulary/words/")
    s.shot(page, "06-mga-salita-at-simbolo", "mga-salita", "Mga Salita at Simbolo", role, "Every word, with the admin's added words")
    go(page, f"{d}/vocabulary/words/?board=Pagkain")
    s.shot(page, "06-mga-salita-at-simbolo", "filter-pagkain", "Mga Salita at Simbolo", role, "Filtered to the Pagkain board")
    go(page, f"{d}/vocabulary/words/")
    open_modal(page, '[data-open-modal="add-word"]')
    s.shot(page, "06-mga-salita-at-simbolo", "add-word-modal", "Mga Salita at Simbolo", role, "＋ Magdagdag ng salita", full=False)
    # The admin's added words are listed after the vocabulary's: on the Pagkain filter's first page.
    go(page, f"{d}/vocabulary/words/?board=Pagkain")
    open_modal(page, '[data-open-modal^="delete-word-"]')
    s.shot(page, "06-mga-salita-at-simbolo", "delete-word-confirm", "Mga Salita at Simbolo", role, "Delete-word confirmation (not confirmed)", full=False)
    go(page, f"{d}/vocabulary/words/?board=Pagkain")
    page.locator('a.secondaryBtn[href*="/vocabulary/words/"]').first.click()
    page.wait_for_load_state("networkidle")
    s.shot(page, "06-mga-salita-at-simbolo", "edit-word-page", "Mga Salita at Simbolo › I-edit", role, "Editing an added word")

    for status, name, what in [("", "lahat", "Lahat"), ("pending", "naghihintay", "Naghihintay"),
                               ("approved", "aprubado", "Aprubado"), ("rejected", "tinanggihan", "Tinanggihan")]:
        go(page, f"{d}/revenue/?status={status}")
        s.shot(page, "07-kita", name, "Kita", role, f"Payments: {what}")
    go(page, f"{d}/revenue/")
    open_modal(page, '[data-open-modal="proof"]')
    page.wait_for_timeout(500)
    s.shot(page, "07-kita", "proof-viewer", "Kita", role, "A proof of payment (SAMPLE PROOF)", full=False)

    go(page, f"{d}/subscriptions/")
    s.shot(page, "08-mga-subscription", "mga-subscription", "Mga Subscription", role, "Guardians per plan, this month's earnings, the waiting payments")
    open_modal(page, '[data-open-modal="proof"]')
    page.wait_for_timeout(500)
    s.shot(page, "08-mga-subscription", "proof-viewer", "Mga Subscription", role, "A waiting payment's proof (SAMPLE PROOF)", full=False)
    go(page, f"{d}/subscriptions/")
    open_modal(page, '[data-open-modal^="approve-"]')
    s.shot(page, "08-mga-subscription", "approve-confirm", "Mga Subscription", role, "Approve confirmation (not confirmed)", full=False)
    go(page, f"{d}/subscriptions/")
    open_modal(page, '[data-open-modal^="reject-"]')
    s.shot(page, "08-mga-subscription", "reject-modal", "Mga Subscription", role, "Reject, asking for the reason (not sent)", full=False)

    go(page, f"{d}/feedback/")
    s.shot(page, "09-feedback-at-mga-isyu", "feedback", "Feedback at mga Isyu", role, "Support messages (open and resolved) and ratings")

    go(page, f"{d}/system/general/")
    s.shot(page, "10-system-general", "general", "System Settings › General", role, "Support contact, maintenance mode (off), GCash with the SAMPLE QR")

    go(page, f"{d}/system/plans/")
    s.shot(page, "11-system-mga-plano", "mga-plano", "System Settings › Mga Plano", role, "Free and SalitAACo Plus, and Mga Limit ng Plano")
    open_modal(page, '[data-open-modal="new-plan"]')
    s.shot(page, "11-system-mga-plano", "add-plan-modal", "System Settings › Mga Plano", role, "＋ Magdagdag ng plano", full=False)
    if page.locator('[data-open-modal^="delete-plan-"]').count():
        go(page, f"{d}/system/plans/")
        open_modal(page, '[data-open-modal^="delete-plan-"]')
        s.shot(page, "11-system-mga-plano", "delete-plan-confirm", "System Settings › Mga Plano", role, "Delete-plan confirmation (not confirmed)", full=False)

    go(page, f"{d}/system/access/")
    s.shot(page, "12-system-access-control", "access-control", "System Settings › Access control", role, "The three admins")
    open_modal(page, '[data-open-modal="add-admin"]')
    s.shot(page, "12-system-access-control", "add-admin-modal", "System Settings › Access control", role, "＋ Magdagdag ng admin", full=False)
    go(page, f"{d}/system/access/")
    open_modal(page, '[data-open-modal^="remove-admin-"]')
    s.shot(page, "12-system-access-control", "remove-admin-confirm", "System Settings › Access control", role, "Remove-admin confirmation (not confirmed)", full=False)

    go(page, f"{d}/system/privacy/")
    s.shot(page, "13-system-privacy", "privacy", "System Settings › Privacy", role, "What is kept, consent versions, old usage counts")
    open_modal(page, '[data-open-modal="purge-usage"]')
    s.shot(page, "13-system-privacy", "purge-usage-confirm", "System Settings › Privacy", role, "Delete-old-counts confirmation (not confirmed)", full=False)

    go(page, f"{d}/board/#home")
    board_screen(page, "home")
    s.shot(page, "14-mga-tile", "own-board-home", "Mga Tile (the admin's own board)", role, "The admin's own board")

    go(page, f"{d}/settings/")
    s.shot(page, "15-hitsura-at-tile", "hitsura-at-tile", "Hitsura at Tile", role, "Tile editing, theme and tile size")

    go(page, f"{d}/profile/")
    s.shot(page, "16-account", "account", "Account", role, "Name, picture, password")
    open_modal(page, '[data-open-modal="delete-account"]')
    s.shot(page, "16-account", "delete-account-confirm", "Account", role, "Delete-account confirmation (not confirmed)", full=False)

    # The one harmless save: General settings sent back unchanged, for its toast.
    go(page, f"{d}/system/general/")
    page.locator("form.settingsFields").first.locator("button[type=submit]").click()
    page.wait_for_load_state("networkidle")
    s.shot(page, "10-system-general", "general-saved-toast", "System Settings › General", role, "The success toast after saving the same values", keep_toast=True, full=False)
    page.context.close()


def capture_maintenance(browser, base, s):
    set_maintenance(True)
    try:
        # Logged out it is the same page, with “Mag-log in” for the link, so one shot is enough.
        page = new_page(browser)
        login(page, base, CHILD)
        s.shot(page, "", "maintenance-page", "Maintenance page", f"Child ({CHILD})", "What everyone but admins gets, children on their board included")
        page.context.close()

        page = new_page(browser)
        login(page, base, ADMIN)
        go(page, f"{base}/dashboard/system/general/")
        s.shot(page, "", "maintenance-admin-general", "System Settings › General", f"Admin ({ADMIN})", "Admins still get in, with maintenance mode on")
        page.context.close()
    finally:
        set_maintenance(False)


# ----- The index -----

def write_readme(index):
    by_side = {}
    for row in index:
        by_side.setdefault(row["file"].split("/")[0], []).append(row)
    lines = [
        "# SalitAACo screenshots",
        "",
        "Every page of SalitAACo at desktop size (1920×1080, light theme), with made-up data. "
        "A `-full.png` next to a shot is the whole page, for pages taller than the screen.",
        "",
        "## Making them again",
        "",
        "From the repository root, with the virtual environment's Python:",
        "",
        "```",
        "pip install -r screenshots/requirements.txt",
        "python -m playwright install chromium",
        "python screenshots/capture.py",
        "```",
        "",
        "`capture.py` reseeds its own database (`screenshots.sqlite3`, with `manage.py seed_screenshots --reset`), "
        "starts the app on a free port with its own uploads folder (`screenshots/_media/`) and no ElevenLabs key, "
        "logs in through `/login/` as each role, takes the shots, rewrites this file and stops the app. "
        "It never touches `db.sqlite3` or `media/`. `--only admin,guardian` takes one side again; "
        "`--no-seed` keeps the current screenshot database.",
        "",
        "Every made-up account's password is `Salita#2026`:",
        "",
        "| Role | Username | Notes |",
        "| --- | --- | --- |",
        f"| Admin | `{ADMIN}` | The demo admin; `paolo.mendoza` and `kristine.bautista` are admins too |",
        f"| Guardian | `{GUARDIAN}` | SalitAACo Plus, three children, two family voices, own boards and tiles |",
        f"| Guardian | `{SECOND_GUARDIAN}` | SalitAACo Plus with two children (the add-a-child window) |",
        "| Guardian | `cristina.lopez` | Free, with a payment waiting for an admin |",
        f"| Child | `{CHILD}` | Miguel Santos, 7, Maricel's child |",
        "",
        "The data is made up: names, payments and ratings. The GCash QR code and every proof of payment are "
        "generated pictures labelled SAMPLE. The family voices' words are copies of the app's shared voice.",
        "",
    ]
    titles = {
        "01-public": "Public website", "02-auth": "Log in and sign up", "03-child": "Child",
        "04-guardian": "Guardian", "05-admin": "Admin", "06-maintenance": "Maintenance mode",
    }
    for side, rows in sorted(by_side.items()):
        lines += [f"## {titles.get(side, side)}", "", "| File | Page | URL | Role | What it shows |", "| --- | --- | --- | --- | --- |"]
        for row in sorted(rows, key=lambda r: r["file"]):
            lines.append(f"| [{row['file']}]({row['file']}) | {row['page']} | `{row['url']}` | {row['role']} | {row['what']} |")
        lines.append("")
    (SHOTS / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", default=",".join(SIDES), help="Comma-separated sides to capture.")
    parser.add_argument("--no-seed", action="store_true", help="Keep the current screenshot database.")
    args = parser.parse_args()
    sides = [side.strip() for side in args.only.split(",") if side.strip()]

    # The index of the sides not taken this time is kept, so --only rewrites the README whole.
    index_file = SHOTS / "_media" / "index.json"
    index = json.loads(index_file.read_text(encoding="utf-8")) if index_file.exists() else []
    index = [row for row in index if row["file"].split("/")[0] not in {SIDE_FOLDERS[side] for side in sides}]

    if not args.no_seed:
        print("Seeding screenshots.sqlite3 …", flush=True)
        manage("seed_screenshots", "--reset")
    check_environment()
    ids = seeded_ids()

    port = free_port()
    base = f"http://localhost:{port}"
    server = start_server(port)
    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch()
            except Exception:
                browser = playwright.chromium.launch(channel="msedge")
            for side in sides:
                print(f"{side}:")
                folder = SHOTS / SIDE_FOLDERS[side]
                if folder.exists():
                    shutil.rmtree(folder)
                s = Shooter(base, index, side)
                if side == "public":
                    page = new_page(browser)
                    capture_public(page, base, s)
                    page.context.close()
                elif side == "auth":
                    page = new_page(browser)
                    capture_auth(page, base, s)
                    page.context.close()
                elif side == "child":
                    page = new_page(browser, block_counting=True)
                    capture_child(page, base, s)
                    page.context.close()
                elif side == "guardian":
                    capture_guardian(browser, base, s, ids)
                elif side == "admin":
                    capture_admin(browser, base, s, ids)
                elif side == "maintenance":
                    capture_maintenance(browser, base, s)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=20)

    index_file.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    write_readme(index)
    counts = {}
    for row in index:
        counts[row["file"].split("/")[0]] = counts.get(row["file"].split("/")[0], 0) + 1
    print("Done:", ", ".join(f"{side} {count}" for side, count in sorted(counts.items())), f"(total {len(index)})")


if __name__ == "__main__":
    main()
