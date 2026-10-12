import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from salitaaco.forms.support.contact_support import ContactSupportForm
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.support_message import SupportMessage
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.children import guardian_children
from salitaaco.utils.perms_check import is_guardian, multi_user_test

logger = logging.getLogger(__name__)

SENT_MESSAGES_SHOWN = 5


@active_nav("support")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_support(request):
    """Guides to the app, and a form for writing to the people who run it."""
    guardian = get_object_or_404(GuardianAccount, user=request.user)
    children = guardian_children(request)

    contact_form = ContactSupportForm(children=children)

    if request.method == "POST":
        contact_form = ContactSupportForm(request.POST, children=children)
        if contact_form.is_valid():
            SupportMessage.objects.create(
                guardian=guardian,
                child=contact_form.chosen_child(),
                message=contact_form.cleaned_data['message'],
            )
            logger.info("Guardian %s sent a support message", request.user.username)
            messages.success(request, "Naipadala na ang mensahe mo. Salamat!")
            return redirect('support')

    context = {
        "contact_form": contact_form,
        "sent_messages": guardian.support_messages.select_related("child").order_by("-created_at")[:SENT_MESSAGES_SHOWN],
    }
    return render(request, 'dashboard/support/support.html', context)
