import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.defaults.administrator_roles import ADMINISTRATOR
from salitaaco.forms.system.add_admin import AddAdminForm
from salitaaco.forms.system.remove_admin import RemoveAdminForm
from salitaaco.utils.account import find_user_account, grant_admin, revoke_admin
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test

logger = logging.getLogger(__name__)


@active_nav("system_access")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_access_control(request):
    """System Settings > Access control: who is an admin, and giving admin access to an account."""
    add_admin_form = AddAdminForm()

    if request.method == "POST":
        add_admin_form = AddAdminForm(request.POST)
        if add_admin_form.is_valid():
            grant_admin(add_admin_form.user)
            logger.warning("Admin %s gave admin access to %s", request.user.username, add_admin_form.user.username)
            messages.success(request, f"Admin na si @{add_admin_form.user.username}.")
            return redirect('system_access')

    admins = list(User.objects.filter(groups__name=ADMINISTRATOR).distinct().order_by("username"))
    for admin in admins:
        admin.account = find_user_account(admin)

    context = {
        "add_admin_form": add_admin_form,
        "show_add_admin_modal": bool(add_admin_form.errors),
        "admins": admins,
    }
    return render(request, 'dashboard/system/access.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_administrator)
@require_POST
def remove_admin(request, user_id):
    user = get_object_or_404(User, pk=user_id, groups__name=ADMINISTRATOR)
    remove_form = RemoveAdminForm(request.POST, acting_user=request.user, target_user=user)

    if remove_form.is_valid():
        revoke_admin(user)
        logger.warning("Admin %s took admin access away from %s", request.user.username, user.username)
        messages.success(request, f"Hindi na admin si @{user.username}.")
    else:
        messages.error(request, remove_form.non_field_errors()[0])
    return redirect('system_access')
