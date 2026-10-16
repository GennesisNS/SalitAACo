"""
System Settings > Privacy: what the app keeps about people, the consent terms
in force, and deleting old per-day usage counts.

This page may be removed. Everything of it is here and in forms/privacy/,
templates/dashboard/privacy/, tests/privacy/, its address in
routes/dashboard/__init__.py and its item in defaults/navigations.py. It has no
model of its own.
"""
import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Min
from django.shortcuts import redirect, render
from django.utils import timezone

from salitaaco.defaults.family_voice import TERMS_VERSION
from salitaaco.forms.privacy.purge_usage import PurgeUsageForm
from salitaaco.models.customization import Customization
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.support_message import SupportMessage
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test

logger = logging.getLogger(__name__)


@active_nav("system_privacy")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_privacy(request):
    purge_form = PurgeUsageForm()

    if request.method == "POST":
        purge_form = PurgeUsageForm(request.POST)
        if purge_form.is_valid():
            cutoff = timezone.localdate() - timedelta(days=purge_form.days())
            deleted, _ = DailyUsage.objects.filter(day__lt=cutoff).delete()
            logger.warning("Admin %s deleted %s per-day usage counts older than %s", request.user.username, deleted, cutoff)
            messages.success(request, f"Nabura na ang {deleted} bilang kada araw na mas luma sa {cutoff.isoformat()}.")
            return redirect('system_privacy')

    # What is kept, in numbers. No names and nothing anyone said with the board.
    kept = [
        {"what": "Mga account", "count": User.objects.count(),
         "note": "Username, password (naka-hash), pangalang ipinapakita, larawan, at edad ng bata kung inilagay."},
        {"what": "Mga larawan at recording ng tile", "count": Customization.objects.count(),
         "note": "Pribado sa may-ari. Nabubura kasama ng account."},
        {"what": "Mga boses ng pamilya", "count": FamilyVoice.objects.count(),
         "note": "Ang recording ay ipinapadala sa ElevenLabs at hindi itinatago rito."},
        {"what": "Mga bilang ng paggamit kada araw", "count": DailyUsage.objects.count(),
         "note": "Bilang lang ng pindot at bukas ng board. Hindi itinatago ang mga pangungusap."},
        {"what": "Mga mensahe sa suporta", "count": SupportMessage.objects.count(),
         "note": "Nabubura kasama ng account ng tagapag-alaga."},
    ]

    context = {
        "purge_form": purge_form,
        "show_purge_modal": bool(purge_form.errors),
        "kept": kept,
        "terms_version": TERMS_VERSION,
        # How many voices were made under each version of the consent terms.
        "consents": FamilyVoice.objects.values("consent_version").annotate(count=Count("family_voice_id")).order_by("-consent_version"),
        "oldest_usage_day": DailyUsage.objects.aggregate(first=Min("day"))["first"],
    }
    return render(request, 'dashboard/privacy/privacy.html', context)
