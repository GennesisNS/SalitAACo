"""
The "Sariling Tile" page: tiles a guardian adds to the boards (the app's or
their own custom boards, set up on a child's Mga Board, see routes/children/boards.py),
which show on their own board and on
every one of their children's. How many a guardian can have depends on their
plan, as an admin sets it on System Settings > General; over it, the oldest
up to it show and the rest are kept, hidden.

A tile is voiced with ElevenLabs when it is added: in the shared voice, kept in
the guardian's own folder under media/ apart from the vocabulary's audio in
static/, and in each of the guardian's family voices (utils/guardian_words.py).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.forms.guardian_words.guardian_word import GuardianWordForm
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.family_voice import elevenlabs_is_set_up
from salitaaco.utils.guardian_boards import shown_guardian_boards
from salitaaco.utils.guardian_words import (
    delete_guardian_word_audio,
    delete_word_usage,
    guardian_word_audio_path,
    guardian_word_audio_urls,
    limit_reached_message,
    on_free_plan,
    shown_guardian_words,
    voice_guardian_word,
    word_limit,
)
from salitaaco.utils.perms_check import is_app_user, is_guardian, multi_user_test

NOT_VOICED = "Hindi pa nagawa ang boses nito, kaya boses muna ng device ang gagamitin. Subukan muli mamaya."


@active_nav("guardian_words")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_guardian_words(request):
    guardian = get_object_or_404(GuardianAccount, user=request.user)
    words = list(guardian.words.all())
    limit = word_limit(guardian)
    on_free = on_free_plan(guardian)
    plus_limit = SiteSetting.load().plus_word_limit
    can_add = len(words) < limit
    limit_message = limit_reached_message("tile", limit, on_free, plus_limit)

    word_form = GuardianWordForm(guardian=guardian)

    if request.method == "POST":
        if not can_add:
            messages.error(request, limit_message)
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

    # A tile shows when it is within the limit and, on a board of the guardian's own, that board shows too.
    shown = {word.pk for word in shown_guardian_words(guardian)}
    own_boards = set(guardian.boards.values_list("name", flat=True))
    shown_boards = {board.name for board in shown_guardian_boards(guardian)}
    audio_urls = guardian_word_audio_urls(words)
    rows = [
        {
            "word": word,
            "audio_url": audio_urls.get(word.word),
            "shown": word.pk in shown and (word.board not in own_boards or word.board in shown_boards),
        }
        for word in words
    ]

    context = {
        "words": rows,
        "word_count": len(words),
        "hidden_count": sum(1 for row in rows if not row["shown"]),
        "limit": limit,
        "can_add": can_add,
        "limit_message": limit_message,
        "offer_plus": on_free and plus_limit > limit,
        "can_voice": elevenlabs_is_set_up(),
        "word_form": word_form,
    }
    return render(request, 'dashboard/guardian_words/guardian_words.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
@require_POST
def remove_guardian_word(request, word_uuid):
    """A guardian removes one of their tiles, shown or not, with its audio and its counts."""
    word = get_object_or_404(GuardianWord, uuid=word_uuid, guardian__user=request.user)
    guardian, text = word.guardian, word.word
    word.delete()
    delete_guardian_word_audio(guardian, text)
    delete_word_usage(guardian, text)
    messages.success(request, f"Nabura na ang “{text}”. Wala na ito sa mga board.")
    return redirect('guardian_words')


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def play_guardian_word(request, word_uuid):
    """A guardian's tile in the shared voice, for the guardian and for the guardian's children."""
    allowed = GuardianWord.objects.filter(
        Q(guardian__user=request.user) | Q(guardian__children__user=request.user)
    ).distinct()
    word = get_object_or_404(allowed.select_related("guardian"), uuid=word_uuid)
    path = guardian_word_audio_path(word)
    if not path.is_file():
        raise Http404()
    response = FileResponse(path.open('rb'), content_type="audio/mpeg")
    response["Cache-Control"] = "private, max-age=86400"
    return response


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
@require_POST
def voice_word(request, word_uuid):
    """Try again to voice a tile whose audio ElevenLabs did not make when it was added. Only a tile that shows."""
    word = get_object_or_404(GuardianWord.objects.select_related("guardian"), uuid=word_uuid, guardian__user=request.user)
    if word.pk not in {shown.pk for shown in shown_guardian_words(word.guardian)}:
        messages.error(request, "Nakatago ang tile na ito dahil lampas na ito sa limit ng plano mo.")
    elif voice_guardian_word(word):
        messages.success(request, f"Nagawa na ang boses ng “{word.word}”.")
    else:
        messages.error(request, NOT_VOICED)
    return redirect('guardian_words')
