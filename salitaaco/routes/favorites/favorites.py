"""
The "Mga Paborito" page: words a guardian puts on a child's Paborito screen.

This page may be removed. Everything of it is here and in forms/favorites/,
models/favorite_word.py (migration 0011), templates/dashboard/favorites/,
tests/favorites/, its two addresses in routes/dashboard/__init__.py and its
item in defaults/navigations.py. The board learns of the words only through
the function registered at the bottom of this file.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.forms.favorites.add_favorite_word import AddFavoriteWordForm
from salitaaco.models.favorite_word import FavoriteWord
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.board import board_data_sources
from salitaaco.utils.children import guardian_child_or_404
from salitaaco.utils.perms_check import is_guardian, multi_user_test


def favorite_words_of(child):
    return child.favorite_words.order_by("created_at", "favorite_word_id")


@active_nav("favorites")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def manage_favorites(request, child_uuid):
    child = guardian_child_or_404(request, child_uuid)

    add_favorite_form = AddFavoriteWordForm(child=child)

    if request.method == "POST":
        add_favorite_form = AddFavoriteWordForm(request.POST, child=child)
        if add_favorite_form.is_valid():
            word = add_favorite_form.cleaned_data['word']
            FavoriteWord.objects.create(child=child, word=word)
            messages.success(request, f"Paborito na ni {child.display_name} ang “{word}”.")
            return redirect('favorites', child_uuid=child.uuid)

    context = {
        "child": child,
        "add_favorite_form": add_favorite_form,
        "favorites": favorite_words_of(child),
    }
    return render(request, 'dashboard/favorites/favorites.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
@require_POST
def remove_favorite(request, child_uuid, favorite_uuid):
    child = guardian_child_or_404(request, child_uuid)
    favorite = get_object_or_404(FavoriteWord, uuid=favorite_uuid, child=child)
    word = favorite.word
    favorite.delete()
    messages.success(request, f"Inalis na ang “{word}” sa mga paborito ni {child.display_name}.")
    return redirect('favorites', child_uuid=child.uuid)


def favorite_words_for_board(child):
    """What the board page is given: the child's favorite words, in the order they were added."""
    if child is None:
        return {}
    return {"favorite_words": [favorite.word for favorite in favorite_words_of(child)]}


if favorite_words_for_board not in board_data_sources:
    board_data_sources.append(favorite_words_for_board)
