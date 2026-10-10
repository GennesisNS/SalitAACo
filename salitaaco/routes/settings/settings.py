from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from salitaaco.defaults.family_voice import PREVIEW_WORD
from salitaaco.forms.children.choose_family_voice import SHARED_VOICE, ChooseFamilyVoiceForm
from salitaaco.forms.settings.tile_size import TileSizeForm
from salitaaco.models.child_account import ChildAccount
from salitaaco.utils.account import get_user_account
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.family_voice import family_voice_preview_url
from salitaaco.utils.perms_check import is_app_user, multi_user_test
from salitaaco.utils.tile_audio import tile_audio_urls


@active_nav("settings")
@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def view_settings(request):
    """How the app looks and works for this user: tile editing, the theme, the tile size and, for a child, the voice."""
    account = get_user_account(request.user)

    tile_size_form = TileSizeForm(initial={"tile_size": account.tile_size})

    # A child whose guardian has made family voices picks which one speaks their tiles.
    child = account if isinstance(account, ChildAccount) else None
    can_choose_voice = bool(child and child.guardian and child.guardian.family_voices.exists())
    voice_form = None
    if can_choose_voice:
        voice_form = ChooseFamilyVoiceForm(
            initial={"family_voice": str(child.family_voice.uuid) if child.family_voice else SHARED_VOICE},
            guardian=child.guardian,
            radios=True,
        )

    if request.method == "POST":
        if "tile_size_form" in request.POST:
            tile_size_form = TileSizeForm(request.POST)
            if tile_size_form.is_valid():
                account.tile_size = tile_size_form.cleaned_data['tile_size']
                account.save()
                messages.success(request, "Naka-save na ang laki ng tile.")
                return redirect('settings')

        if "voice_form" in request.POST and can_choose_voice:
            voice_form = ChooseFamilyVoiceForm(request.POST, guardian=child.guardian, radios=True)
            if voice_form.is_valid():
                chosen = voice_form.cleaned_data['family_voice']
                child.family_voice = child.guardian.family_voices.get(uuid=chosen) if chosen else None
                child.save()
                messages.success(request, "Naka-save na ang boses ng iyong mga tile.")
                return redirect('settings')

    # Each choice with what ▶ plays: the shared voice, then each family voice, saying the preview word.
    voice_choices = []
    if voice_form:
        previews = [tile_audio_urls().get(PREVIEW_WORD)] + [family_voice_preview_url(voice) for voice in voice_form.voices]
        voice_choices = list(zip(voice_form["family_voice"], previews))

    context = {
        "tile_size_form": tile_size_form,
        "tile_size": account.tile_size,
        "voice_form": voice_form,
        "voice_choices": voice_choices,
    }
    return render(request, 'dashboard/settings/settings.html', context)
