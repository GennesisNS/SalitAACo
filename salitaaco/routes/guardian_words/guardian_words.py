"""
The "Sariling Tile" page: tiles a guardian adds to the boards (the app's or
their own custom boards, set up on a child's Mga Board, see routes/children/boards.py),
which show on their own board and on
every one of their children's. How many a guardian can have depends on their
plan, as an admin sets it on System Settings > Mga Plano; over it, the oldest
up to it show and the rest are kept, hidden.

A tile is voiced with ElevenLabs when it is added: in the shared voice, kept in
the guardian's own folder under media/ apart from the vocabulary's audio in
static/, and in each of the guardian's family voices (utils/guardian_words.py).
Its symbol is an emoji or, on Plus, an uploaded picture, which only the
guardian and their children are served.

A tile can be changed afterwards ("I-edit"): its word, board and symbol. It
keeps the day it was added; a new word takes the old one's counts along and is
voiced again (utils/guardian_words.py).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.forms.guardian_words.guardian_word import GuardianWordForm
from salitaaco.forms.picture_choice import picture_kind
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.family_voice import elevenlabs_is_set_up
from salitaaco.utils.guardian_boards import shown_guardian_boards
from salitaaco.utils.guardian_words import (
    delete_guardian_word,
    guardian_word_audio_path,
    guardian_word_audio_urls,
    limit_reached_message,
    on_free_plan,
    rename_guardian_word,
    revoice_renamed_word,
    shown_guardian_words,
    voice_guardian_word,
    word_limit,
)
from salitaaco.utils.perms_check import is_app_user, is_guardian, multi_user_test
from salitaaco.utils.uploads import icon_image_url

NOT_VOICED = "Hindi pa nagawa ang boses nito, kaya boses muna ng device ang gagamitin. Subukan muli mamaya."


def edit_form(word, data=None, files=None):
    """
    The form that changes one of the guardian's tiles, filled in with it. Its
    fields are named after the tile, so that every tile's form can be on the page.
    """
    return GuardianWordForm(
        data, files,
        prefix=f"word-{word.pk}",
        guardian=word.guardian,
        editing=word,
        initial={"board": word.board, "word": word.word, "emoji": word.emoji, "icon_kind": picture_kind(word)},
    )


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
    edit_forms = {word.pk: edit_form(word) for word in words}
    open_modal = None

    # A tile shows when it is within the limit and, on a board of the guardian's own, that board shows too.
    shown = {word.pk for word in shown_guardian_words(guardian)}
    own_boards = set(guardian.boards.values_list("name", flat=True))
    shown_boards = {board.name for board in shown_guardian_boards(guardian)}

    def is_shown(word):
        return word.pk in shown and (word.board not in own_boards or word.board in shown_boards)

    if request.method == "POST":
        if "edit_word_form" in request.POST:
            word = next((word for word in words if str(word.uuid) == request.POST["edit_word_form"]), None)
            if word is None:
                raise Http404()
            form = edit_forms[word.pk] = edit_form(word, request.POST, request.FILES)
            if form.is_valid():
                old = word.word
                with transaction.atomic():
                    word.board = form.cleaned_data['board']
                    word.save()
                    rename_guardian_word(word, form.cleaned_data['word'])
                    form.save_picture(word)
                messages.success(request, f"Naka-save na ang “{word.word}”.")
                # A hidden tile is voiced when it shows again, with "Gawin ang boses".
                if is_shown(word) and not revoice_renamed_word(word, old):
                    messages.error(request, NOT_VOICED)
                return redirect('guardian_words')
            open_modal = f"edit-word-{word.uuid}"

        else:
            if not can_add:
                messages.error(request, limit_message)
                return redirect('guardian_words')

            word_form = GuardianWordForm(request.POST, request.FILES, guardian=guardian)
            if word_form.is_valid():
                with transaction.atomic():
                    word = GuardianWord.objects.create(
                        guardian=guardian,
                        board=word_form.cleaned_data['board'],
                        word=word_form.cleaned_data['word'],
                    )
                    word_form.save_picture(word)
                messages.success(request, f"Naidagdag na ang “{word.word}” sa board na “{word.board}”.")
                if not voice_guardian_word(word):
                    messages.error(request, NOT_VOICED)
                return redirect('guardian_words')

    audio_urls = guardian_word_audio_urls(words)
    rows = [
        {
            "word": word,
            "icon_url": icon_image_url("guardian_word_image", word),
            "audio_url": audio_urls.get(word.word),
            "shown": is_shown(word),
            "edit_form": edit_forms[word.pk],
            # Its form was sent and was not valid: the window reopens to say why.
            "reopen": open_modal == f"edit-word-{word.uuid}",
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
    """A guardian removes one of their tiles, shown or not, with its picture, its audio and its counts."""
    word = get_object_or_404(GuardianWord.objects.select_related("guardian"), uuid=word_uuid, guardian__user=request.user)
    text = word.word
    delete_guardian_word(word)
    messages.success(request, f"Nabura na ang “{text}”. Wala na ito sa mga board.")
    return redirect('guardian_words')


def family_word_or_404(request, word_uuid):
    """A guardian's tile, for the guardian and for the guardian's children only."""
    allowed = GuardianWord.objects.filter(
        Q(guardian__user=request.user) | Q(guardian__children__user=request.user)
    ).distinct()
    return get_object_or_404(allowed.select_related("guardian"), uuid=word_uuid)


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def play_guardian_word(request, word_uuid):
    """A guardian's tile in the shared voice, for the guardian and for the guardian's children."""
    word = family_word_or_404(request, word_uuid)
    path = guardian_word_audio_path(word)
    if not path.is_file():
        raise Http404()
    response = FileResponse(path.open('rb'), content_type="audio/mpeg")
    response["Cache-Control"] = "private, max-age=86400"
    return response


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def view_guardian_word_image(request, word_uuid):
    """A guardian's tile's uploaded picture, for the guardian and for the guardian's children."""
    word = family_word_or_404(request, word_uuid)
    if not word.has_icon_image:
        raise Http404()
    response = FileResponse(word.icon_image.open('rb'), content_type=word.icon_mime or "application/octet-stream")
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
