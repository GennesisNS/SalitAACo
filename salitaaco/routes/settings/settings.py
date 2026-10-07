from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_app_user, multi_user_test


@active_nav("settings")
@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def view_settings(request):
    """How the app looks and works for this user: tile editing and the theme."""
    return render(request, 'dashboard/settings/settings.html')
