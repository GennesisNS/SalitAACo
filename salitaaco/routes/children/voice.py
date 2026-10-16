from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from salitaaco.defaults.family_voice import PREVIEW_WORD
from salitaaco.forms.children.choose_family_voice import SHARED_VOICE, ChooseFamilyVoiceForm
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.children import guardian_child_or_404
from salitaaco.utils.family_voice import family_voice_preview_url
from salitaaco.utils.perms_check import is_guardian, multi_user_test
from salitaaco.utils.tile_audio import tile_audio_urls


@active_nav("child_voice")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def choose_child_voice(request, child_uuid):
    """Whose voice speaks a child's tiles: the app's, or one of the family's voices."""
    child = guardian_child_or_404(request, child_uuid)

    voice_form = ChooseFamilyVoiceForm(
        initial={"family_voice": str(child.family_voice.uuid) if child.family_voice else SHARED_VOICE},
        guardian=child.guardian,
        radios=True,
    )

    if request.method == "POST" and "voice_form" in request.POST:
        voice_form = ChooseFamilyVoiceForm(request.POST, guardian=child.guardian, radios=True)
        if voice_form.is_valid():
            chosen = voice_form.cleaned_data['family_voice']
            child.family_voice = child.guardian.family_voices.get(uuid=chosen) if chosen else None
            child.save()
            messages.success(request, f"Naka-save na ang boses na maririnig ni {child.display_name}.")
            return redirect('child_voice', child_uuid=child.uuid)

    # Each choice with what ▶ plays: the shared voice, then each family voice, saying the preview word.
    previews = [tile_audio_urls().get(PREVIEW_WORD)] + [family_voice_preview_url(voice) for voice in voice_form.voices]

    context = {
        "child": child,
        "voice_form": voice_form,
        "voice_choices": list(zip(voice_form["family_voice"], previews)),
        "has_family_voices": bool(voice_form.voices),
    }
    return render(request, 'dashboard/children/voice.html', context)
