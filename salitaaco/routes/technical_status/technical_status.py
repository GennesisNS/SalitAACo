"""
System Settings > Technical status: whether the pieces the app runs on are in
order, and the latest errors from its log.

This page may be removed. Everything of it is here and in
templates/dashboard/technical_status/, tests/technical_status/, its address in
routes/dashboard/__init__.py and its item in defaults/navigations.py. It has no
model and no form: it only reads.
"""
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.shortcuts import render

from salitaaco.models.site_setting import SiteSetting
from salitaaco.templatetags.format_bytes import format_bytes
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.analytics import storage_bytes
from salitaaco.utils.family_voice import elevenlabs_is_set_up
from salitaaco.utils.perms_check import is_administrator, multi_user_test
from salitaaco.utils.tile_audio import tile_audio_urls, tile_words

ERRORS_SHOWN = 10
# How much of the end of the log is read to find them.
LOG_TAIL_BYTES = 200 * 1024


def unapplied_migrations():
    executor = MigrationExecutor(connection)
    return len(executor.migration_plan(executor.loader.graph.leaf_nodes()))


def recent_errors(limit=ERRORS_SHOWN):
    """The last error lines of the app's log, newest first. Empty when there is no log to read."""
    path = settings.LOG_FILE
    try:
        with open(path, "rb") as log:
            log.seek(max(0, os.path.getsize(path) - LOG_TAIL_BYTES))
            lines = log.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return []
    errors = [line for line in lines if " ERROR " in line]
    return errors[-limit:][::-1]


@active_nav("system_status")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_technical_status(request):
    try:
        connection.ensure_connection()
        pending = unapplied_migrations()
        database_ok = True
    except Exception:  # whatever the driver raises: the page's job is to report it, not to fail with it
        pending = None
        database_ok = False

    voiced = len(tile_audio_urls()) if database_ok else 0
    words = len(tile_words()) if database_ok else 0
    maintenance = SiteSetting.load().maintenance_mode if database_ok else False

    # Each check: what it is, whether it is in order, and what was found.
    checks = [
        {"name": "Database", "ok": database_ok,
         "detail": f"{connection.vendor}: nakakonekta" if database_ok else f"{connection.vendor}: hindi makakonekta"},
        {"name": "Mga migration", "ok": pending == 0,
         "detail": "Naka-apply na lahat" if pending == 0 else (
             f"{pending} ang hindi pa naka-apply: patakbuhin ang “python manage.py migrate”" if pending else "Hindi matiyak")},
        {"name": "Debug mode", "ok": not settings.DEBUG,
         "detail": "Naka-off" if not settings.DEBUG else "Naka-on: para lang ito sa development, hindi sa live na site"},
        {"name": "Maintenance mode", "ok": not maintenance,
         "detail": "Naka-off" if not maintenance else "Naka-on: mga admin lang ang nakakagamit ng app"},
        {"name": "ElevenLabs (boses ng pamilya)", "ok": elevenlabs_is_set_up(),
         "detail": "May API key" if elevenlabs_is_set_up() else "Walang API key: hindi makakagawa ng boses ng pamilya"},
        {"name": "Karaniwang boses ng mga tile", "ok": words > 0 and voiced == words,
         "detail": f"{voiced} sa {words} salita ang may audio"
                   + ("" if voiced == words else ": patakbuhin ang “python manage.py generate_tile_audio”")},
    ]

    context = {
        "checks": checks,
        "problem_count": sum(1 for check in checks if not check["ok"]),
        "storage": format_bytes(storage_bytes()),
        "errors": recent_errors(),
    }
    return render(request, 'dashboard/technical_status/technical_status.html', context)
