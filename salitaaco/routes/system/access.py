import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.defaults.administrator_roles import ADMINISTRATOR
from salitaaco.forms.system.add_admin import AddAdminForm
from salitaaco.forms.system.remove_admin import RemoveAdminForm
from salitaaco.utils.account import create_admin, delete_user_account, find_user_account
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test

logger = logging.getLogger(__name__)


@active_nav("system_access")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_access_control(request):
    """
    System Settings > Access control: who the admins are, making a new admin
    account, and deleting one. Admins are accounts of their own, never a
    guardian's or a child's.
    """
    add_admin_form = AddAdminForm()

    if request.method == "POST":
        add_admin_form = AddAdminForm(request.POST)
        if add_admin_form.is_valid():
            admin = create_admin(
                username=add_admin_form.cleaned_data['username'],
                display_name=add_admin_form.cleaned_data['display_name'],
                password=add_admin_form.cleaned_data['password'],
            )
            logger.warning("Admin %s made the admin account %s", request.user.username, admin.username)
            messages.success(request, f"Nagawa na ang admin account na @{admin.username}.")
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
    """Delete another admin's account. An admin account holds nothing else, so nothing else goes with it."""
    user = get_object_or_404(User, pk=user_id, groups__name=ADMINISTRATOR)
    remove_form = RemoveAdminForm(request.POST, acting_user=request.user, target_user=user)

    if remove_form.is_valid():
        username = user.username
        delete_user_account(user)
        logger.warning("Admin %s deleted the admin account %s", request.user.username, username)
        messages.success(request, f"Nabura na ang admin account na @{username}.")
    else:
        messages.error(request, remove_form.non_field_errors()[0])
    return redirect('system_access')
