"""
The "Sariling Tile" page: tiles a guardian on a paid plan adds to the boards,
which show on their own board and on every one of their children's. How many
a guardian can have is set on System Settings > General. While the guardian
is not on a paid plan, their tiles are kept but not shown, and none can be added.

A tile is voiced with ElevenLabs when it is added: in the shared voice and in
each of the guardian's family voices (utils/guardian_words.py).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.forms.guardian_words.guardian_word import GuardianWordForm
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.family_voice import elevenlabs_is_set_up
from salitaaco.utils.guardian_words import (
    can_add_words,
    delete_guardian_word_audio,
    guardian_word_limit,
    voice_guardian_word,
)
from salitaaco.utils.perms_check import is_guardian, multi_user_test
from salitaaco.utils.tile_audio import tile_audio_urls

NOT_VOICED = "Hindi pa nagawa ang boses nito, kaya boses muna ng device ang gagamitin. Subukan muli mamaya."


@active_nav("guardian_words")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_guardian_words(request):
    guardian = get_object_or_404(GuardianAccount, user=request.user)
    words = guardian.words.all()
    limit = guardian_word_limit()
    on_paid_plan = can_add_words(guardian)
    at_limit = words.count() >= limit

    word_form = GuardianWordForm(guardian=guardian)

    if request.method == "POST":
        if not on_paid_plan:
            messages.error(request, "Para sa SalitAACo Plus lang ang pagdagdag ng sariling tile.")
            return redirect('guardian_words')
        if at_limit:
            messages.error(request, f"Naabot mo na ang {limit} na sariling tile. Magbura muna ng isa para makapagdagdag.")
            return redirect('guardian_words')

        word_form = GuardianWordForm(request.POST, guardian=guardian)
        if word_form.is_valid():
            word = GuardianWord.objects.create(
                guardian=guardian,
                board=word_form.cleaned_data['board'],
                word=word_form.cleaned_data['word'],
                emoji=word_form.cleaned_data['emoji'],
            )
            messages.success(request, f"Naidagdag na ang “{word.word}” sa board na “{word.board}”.")
            if not voice_guardian_word(word):
                messages.error(request, NOT_VOICED)
            return redirect('guardian_words')

    audio_urls = tile_audio_urls([word.word for word in words])

    context = {
        "words": [{"word": word, "audio_url": audio_urls.get(word.word)} for word in words],
        "word_count": words.count(),
        "limit": limit,
        "on_paid_plan": on_paid_plan,
        "at_limit": at_limit,
        "can_voice": on_paid_plan and elevenlabs_is_set_up(),
        "word_form": word_form,
    }
    return render(request, 'dashboard/guardian_words/guardian_words.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
@require_POST
def remove_guardian_word(request, word_uuid):
    """A guardian removes one of their tiles, on a paid plan or not."""
    word = get_object_or_404(GuardianWord, uuid=word_uuid, guardian__user=request.user)
    guardian, text = word.guardian, word.word
    word.delete()
    delete_guardian_word_audio(guardian, text)
    messages.success(request, f"Nabura na ang “{text}”. Wala na ito sa mga board.")
    return redirect('guardian_words')


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
@require_POST
def voice_word(request, word_uuid):
    """Try again to voice a tile whose audio ElevenLabs did not make when it was added."""
    word = get_object_or_404(GuardianWord.objects.select_related("guardian"), uuid=word_uuid, guardian__user=request.user)
    if not can_add_words(word.guardian):
        messages.error(request, "Para sa SalitAACo Plus lang ang sariling tile.")
    elif voice_guardian_word(word):
        messages.success(request, f"Nagawa na ang boses ng “{word.word}”.")
    else:
        messages.error(request, NOT_VOICED)
    return redirect('guardian_words')
