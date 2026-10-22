import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.defaults.vocabulary import CATEGORIES
from salitaaco.forms.picture_choice import picture_kind
from salitaaco.forms.vocabulary.search_word import SearchWordForm
from salitaaco.forms.vocabulary.word import WordForm
from salitaaco.models.added_word import AddedWord
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_administrator, is_app_user, multi_user_test
from salitaaco.utils.tile_audio import VERB_ASPECTS
from salitaaco.utils.uploads import icon_image_url

logger = logging.getLogger(__name__)

WORDS_PER_PAGE = 20


def every_word():
    """
    Every word of every board as a row: the default words in board order, a
    verb with its three forms, then the words an admin added. Only the added
    ones carry `added`, the AddedWord, and can be changed or deleted; their
    symbol may be an uploaded picture (`icon_url`).
    """
    rows = []
    for category in CATEGORIES:
        for item in category["items"]:
            verb = item.get("verb")
            rows.append({
                "emoji": item["e"],
                "icon_url": None,
                "word": " · ".join(verb[aspect] for aspect in VERB_ASPECTS) if verb else item["w"],
                "board": category["name"],
                "added": None,
            })
    for added in AddedWord.objects.order_by("created_at", "added_word_id"):
        rows.append({
            "emoji": added.emoji,
            "icon_url": icon_image_url("added_word_image", added),
            "word": added.word,
            "board": added.board,
            "added": added,
        })
    return rows


@active_nav("words")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_words(request):
    """Every word and its symbol, and the form that adds a word to a board."""
    search_form = SearchWordForm(request.GET or None)
    word_form = WordForm()

    if request.method == "POST":
        word_form = WordForm(request.POST, request.FILES)
        if word_form.is_valid():
            with transaction.atomic():
                added = AddedWord.objects.create(
                    board=word_form.cleaned_data['board'],
                    word=word_form.cleaned_data['word'],
                )
                word_form.save_picture(added)
            logger.info("Admin %s added the word %s to %s", request.user.username, added.word, added.board)
            messages.success(request, f"Naidagdag na ang “{added.word}” sa board na “{added.board}”.")
            return redirect('words')

    query, board = search_form.filters()
    rows = [
        row for row in every_word()
        if (not query or query in row["word"].lower()) and (not board or row["board"] == board)
    ]

    context = {
        "search_form": search_form,
        "word_form": word_form,
        "show_add_word_modal": bool(word_form.errors),
        "words": paginate(rows, request.GET.get("page", 1), WORDS_PER_PAGE),
        "word_count": len(rows),
        "added_count": AddedWord.objects.count(),
    }
    return render(request, 'dashboard/vocabulary/words.html', context)


@active_nav("words")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def edit_word(request, word_uuid):
    """Change a word an admin added. The default words are not changed here: they are the app's vocabulary."""
    added = get_object_or_404(AddedWord, uuid=word_uuid)

    word_form = WordForm(
        initial={"board": added.board, "word": added.word, "emoji": added.emoji, "icon_kind": picture_kind(added)},
        editing=added,
    )

    if request.method == "POST":
        word_form = WordForm(request.POST, request.FILES, editing=added)
        if word_form.is_valid():
            with transaction.atomic():
                added.board = word_form.cleaned_data['board']
                added.word = word_form.cleaned_data['word']
                added.save()
                word_form.save_picture(added)
            messages.success(request, f"Naka-save na ang “{added.word}”.")
            return redirect('words')

    context = {
        "added": added,
        "icon_url": icon_image_url("added_word_image", added),
        "word_form": word_form,
    }
    return render(request, 'dashboard/vocabulary/word.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_administrator)
@require_POST
def delete_word(request, word_uuid):
    added = get_object_or_404(AddedWord, uuid=word_uuid)
    word = added.word
    added.remove_icon_image(save=False)
    added.delete()
    logger.info("Admin %s deleted the added word %s", request.user.username, word)
    messages.success(request, f"Nabura na ang “{word}”. Wala na ito sa mga board.")
    return redirect('words')


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def view_added_word_image(request, word_uuid):
    """The uploaded picture of a word an admin added: a tile on everyone's boards, so for every account."""
    added = get_object_or_404(AddedWord, uuid=word_uuid)
    if not added.has_icon_image:
        raise Http404()
    response = FileResponse(added.icon_image.open('rb'), content_type=added.icon_mime or "application/octet-stream")
    response["Cache-Control"] = "private, max-age=86400"
    return response
