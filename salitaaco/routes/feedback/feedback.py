"""
The "Feedback at mga Isyu" page: what users think of the app (their ratings)
and what guardians wrote to support, with a way to mark a message as dealt with.

This page may be removed. Everything of it is here and in
templates/dashboard/feedback/, tests/feedback/, its two addresses in
routes/dashboard/__init__.py and its item in defaults/navigations.py. It has no
model of its own: it reads Rating and SupportMessage, which belong to the
board's rating form and to the Tulong at Suporta page.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from salitaaco.models.rating import Rating
from salitaaco.models.support_message import SupportMessage
from salitaaco.utils import analytics
from salitaaco.utils.account import ACCOUNT_RELATIONS, find_user_account
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_administrator, multi_user_test


@active_nav("feedback")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_feedback(request):
    # The open messages first, then the ones dealt with; newest first within each.
    support_messages = SupportMessage.objects.select_related("guardian__user", "child").order_by(
        F("resolved_at").asc(nulls_first=True), "-created_at",
    )
    messages_page = paginate(support_messages, request.GET.get("messages_page", 1))

    ratings = Rating.objects.select_related(
        *[f"user__{relation}" for relation in ACCOUNT_RELATIONS]
    ).order_by("-updated_at")
    ratings_page = paginate(ratings, request.GET.get("ratings_page", 1))
    # The account behind each rating tells the template the name to show.
    for rating in ratings_page:
        rating.user.account = find_user_account(rating.user)

    context = {
        "overview": analytics.overview(),
        "rating_distribution": analytics.rating_distribution(),
        "ratings": ratings_page,
        "support_messages": messages_page,
        "open_count": support_messages.filter(resolved_at__isnull=True).count(),
    }
    return render(request, 'dashboard/feedback/feedback.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_administrator)
@require_POST
def resolve_support_message(request, message_uuid):
    """Mark a guardian's message as dealt with, or as open again."""
    message = get_object_or_404(SupportMessage, uuid=message_uuid)
    if message.is_resolved:
        message.resolved_at = None
        messages.success(request, "Bukas na muli ang mensahe.")
    else:
        message.resolved_at = timezone.now()
        messages.success(request, "Namarkahan nang naayos ang mensahe.")
    message.save()
    return redirect(f"{reverse('feedback')}#messages")
