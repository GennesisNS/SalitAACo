from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from salitaaco.forms.settings.tile_size import TileSizeForm
from salitaaco.utils.account import get_user_account
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_app_user, multi_user_test


@active_nav("settings")
@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def view_settings(request):
    """How the app looks and works for this user: tile editing, the theme and the tile size."""
    account = get_user_account(request.user)

    tile_size_form = TileSizeForm(initial={"tile_size": account.tile_size})

    if request.method == "POST":
        if "tile_size_form" in request.POST:
            tile_size_form = TileSizeForm(request.POST)
            if tile_size_form.is_valid():
                account.tile_size = tile_size_form.cleaned_data['tile_size']
                account.save()
                messages.success(request, "Naka-save na ang laki ng tile.")
                return redirect('settings')

    context = {
        "tile_size_form": tile_size_form,
        "tile_size": account.tile_size,
    }
    return render(request, 'dashboard/settings/settings.html', context)
