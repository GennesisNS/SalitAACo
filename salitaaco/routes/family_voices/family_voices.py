import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from salitaaco.backends.text_to_speech.elevenlabs import ElevenLabsError
from salitaaco.defaults.family_voice import PREVIEW_WORD, READING_PARAGRAPH, TERMS_VERSION, WORDS_PER_REQUEST
from salitaaco.forms.family_voices.add_family_voice import AddFamilyVoiceForm
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.family_voice import (
    create_family_voice,
    delete_family_voice,
    elevenlabs_is_set_up,
    family_voice_directory,
    family_voice_preview_url,
    family_voice_progress,
    generate_family_voice_words,
)
from salitaaco.utils.perms_check import is_app_user, is_guardian, multi_user_test
from salitaaco.utils.tile_audio import tile_word_slug

logger = logging.getLogger(__name__)


@active_nav("family_voices")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_family_voices(request):
    guardian = get_object_or_404(GuardianAccount, user=request.user)

    add_family_voice_form = AddFamilyVoiceForm()

    if request.method == "POST" and elevenlabs_is_set_up():
        add_family_voice_form = AddFamilyVoiceForm(request.POST, request.FILES)
        if add_family_voice_form.is_valid():
            name = add_family_voice_form.cleaned_data['name']
            try:
                create_family_voice(guardian, name, add_family_voice_form.cleaned_data['sample'])
            except ElevenLabsError:
                add_family_voice_form.add_error(None, "Hindi nagawa ang boses ngayon. Pakisubukan muli mamaya.")
            else:
                messages.success(request, f"Nagawa na ang boses ni {name}. Ginagawa na ang mga salita nito.")
                return redirect('family_voices')

    voices = []
    for voice in guardian.family_voices.order_by("created_at"):
        done, total = family_voice_progress(voice)
        voices.append({
            "voice": voice,
            "done": done,
            "total": total,
            "percent": round(done / total * 100) if total else 100,
            "children": [child.display_name for child in voice.children.order_by("display_name")],
            "generate_url": reverse('generate_family_voice', args=[voice.uuid]),
            "preview_url": reverse('play_family_voice_word', args=[voice.uuid, tile_word_slug(PREVIEW_WORD)]),
            # ▶ Subukan can only play once the preview word has been generated in this voice.
            "has_preview": family_voice_preview_url(voice) is not None,
        })

    context = {
        "elevenlabs_is_set_up": elevenlabs_is_set_up(),
        "add_family_voice_form": add_family_voice_form,
        "show_add_family_voice_modal": bool(add_family_voice_form.errors),
        "voices": voices,
        "reading_paragraph": READING_PARAGRAPH,
        "terms_version": TERMS_VERSION,
    }
    return render(request, 'dashboard/family_voices/family_voices.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
@require_POST
def generate_family_voice(request, family_voice_uuid):
    """
    Generate the next few tile words in a voice. The family voices page calls
    this again and again until every word is done, showing the progress.
    """
    voice = get_object_or_404(FamilyVoice, uuid=family_voice_uuid, guardian__user=request.user)
    try:
        done, total = generate_family_voice_words(voice, WORDS_PER_REQUEST)
    except ElevenLabsError:
        done, total = family_voice_progress(voice)
        return JsonResponse({
            "ok": False,
            "done": done,
            "total": total,
            "error": "Natigil ang paggawa ng mga salita. Buksan muli ang pahina para ituloy.",
        }, status=502)
    return JsonResponse({"ok": True, "done": done, "total": total, "finished": done == total})


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def play_family_voice_word(request, family_voice_uuid, word_slug):
    """One tile word in a family voice, for the guardian and for the guardian's children."""
    allowed = FamilyVoice.objects.filter(
        Q(guardian__user=request.user) | Q(guardian__children__user=request.user)
    ).distinct()
    voice = get_object_or_404(allowed, uuid=family_voice_uuid)

    path = family_voice_directory(voice) / f"{word_slug}.mp3"
    if not path.is_file():
        raise Http404()
    response = FileResponse(path.open('rb'), content_type="audio/mpeg")
    response["Cache-Control"] = "private, max-age=86400"
    return response


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
@require_POST
def remove_family_voice(request, family_voice_uuid):
    voice = get_object_or_404(FamilyVoice, uuid=family_voice_uuid, guardian__user=request.user)
    name = voice.name
    try:
        delete_family_voice(voice)
    except ElevenLabsError:
        messages.error(request, f"Hindi nabura ang boses ni {name} ngayon. Pakisubukan muli mamaya.")
    else:
        messages.success(request, f"Permanente nang nabura ang boses ni {name}.")
    return redirect('family_voices')
