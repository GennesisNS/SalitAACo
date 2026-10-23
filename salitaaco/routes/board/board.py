import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from salitaaco.defaults.board import FEELINGS_BOARD
from salitaaco.defaults.vocabulary import VERB_CATEGORY
from salitaaco.forms.board.upload_tile_image import UploadTileImageForm
from salitaaco.forms.board.upload_tile_sound import UploadTileSoundForm
from salitaaco.forms.rating.submit_rating import SubmitRatingForm
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.customization import Customization
from salitaaco.models.rating import Rating
from salitaaco.utils.account import get_user_account
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.board import board_words, quick_words
from salitaaco.utils.children import guardian_child_or_404
from salitaaco.utils.family_voice import family_voice_urls
from salitaaco.utils.guardian_boards import board_guardian, boards_of
from salitaaco.utils.guardian_words import guardian_word_audio_urls, shown_guardian_words
from salitaaco.utils.perms_check import is_app_user, multi_user_test
from salitaaco.utils.tile_audio import tile_audio_urls
from salitaaco.utils.uploads import random_upload_name
from salitaaco.utils.word_usage import frequent_words

logger = logging.getLogger(__name__)


def first_form_error(form):
    for errors in form.errors.values():
        return errors[0]
    return ""


@active_nav("board", "home")
@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def view_board(request, child_uuid=None):
    # The board shown is the user's own, unless a guardian opened the board of
    # one of their children to set up its tiles. `owner` is whose tiles these are.
    managed_child = None
    owner = request.user
    board_url = reverse('board')
    if child_uuid is not None:
        managed_child = guardian_child_or_404(request, child_uuid)
        owner = managed_child.user
        board_url = reverse('child_board', args=[managed_child.uuid])
        request.active_nav_ids = ("children",)

    user_rating = Rating.objects.filter(user=request.user).first()

    # The child whose board this is (None on a guardian's or an admin's own), and its boards.
    owner_child = managed_child or ChildAccount.objects.filter(user=owner).select_related("family_voice").first()
    categories = boards_of(owner, owner_child)
    # A picture or a recording is only for a tile these boards have.
    words = board_words(categories)

    tile_image_form = UploadTileImageForm()
    tile_sound_form = UploadTileSoundForm()
    rating_form = SubmitRatingForm(initial={
        "rating": user_rating.rating if user_rating else "",
        "comment": (user_rating.comment or "") if user_rating else "",
    })

    if request.method == "POST":
        if "tile_image_form" in request.POST:
            tile_image_form = UploadTileImageForm(request.POST, request.FILES, words=words)
            if tile_image_form.is_valid():
                image = tile_image_form.cleaned_data['image']
                customization, _ = Customization.objects.get_or_create(
                    user=owner,
                    word=tile_image_form.cleaned_data['word'],
                )
                customization.set_image(random_upload_name(image.content_type), image, image.content_type)
                messages.success(request, "Nai-save na ang larawan ng tile.")
            else:
                # The upload form has no visible fields, so its error is shown as a toast.
                messages.error(request, first_form_error(tile_image_form))
            return redirect(board_url)

        if "tile_sound_form" in request.POST:
            tile_sound_form = UploadTileSoundForm(request.POST, request.FILES, words=words)
            if tile_sound_form.is_valid():
                sound = tile_sound_form.cleaned_data['sound']
                customization, _ = Customization.objects.get_or_create(
                    user=owner,
                    word=tile_sound_form.cleaned_data['word'],
                )
                customization.set_sound(random_upload_name(sound.content_type), sound, sound.content_type)
                messages.success(request, "Nai-save na ang tunog ng tile.")
            else:
                messages.error(request, first_form_error(tile_sound_form))
            return redirect(board_url)

        if "rating_form" in request.POST:
            rating_form = SubmitRatingForm(request.POST)
            if rating_form.is_valid():
                Rating.objects.update_or_create(
                    user=request.user,
                    defaults={
                        "rating": rating_form.cleaned_data['rating'],
                        "comment": rating_form.cleaned_data['comment'],
                    },
                )
                messages.success(request, "Salamat sa iyong rating!")
                return redirect(board_url)

    customizations = [
        {
            "uuid": str(customization.uuid),
            "word": customization.word,
            "has_image": customization.has_image,
            "has_sound": customization.has_sound,
            "image_url": f"{reverse('view_customization_image', args=[customization.uuid])}?v={customization.version}",
            "sound_url": f"{reverse('view_customization_sound', args=[customization.uuid])}?v={customization.version}",
            "reset_url": reverse('reset_customization', args=[customization.uuid]),
        }
        for customization in Customization.objects.filter(user=owner)
    ]

    # The voice for tiles nobody recorded by hand: the child's family voice where it
    # already has the word, otherwise the app's shared voice.
    # The guardian's own tiles that show, up to their plan's limit.
    own_words = shown_guardian_words(board_guardian(owner, owner_child))
    tile_audio = tile_audio_urls()
    tile_audio.update(guardian_word_audio_urls(own_words))
    if owner_child and owner_child.family_voice:
        tile_audio.update(family_voice_urls(owner_child.family_voice))

    context = {
        "managed_child": managed_child,
        # Drawn at the size its owner chose in Settings, so a guardian sees a child's board as the child does.
        "tile_size": (managed_child or get_user_account(request.user)).tile_size,
        "tile_image_form": tile_image_form,
        "tile_sound_form": tile_sound_form,
        "rating_form": rating_form,
        "show_rating_modal": bool(rating_form.errors),
        "board_data": {
            # The app's boards and the family's own, with the family's own tiles;
            # a child's are the ones their guardian left on.
            "categories": categories,
            "verb_category": VERB_CATEGORY,
            # The Home screen: the quick words, then the board of feelings.
            "quick_words": quick_words(),
            "feelings_board": FEELINGS_BOARD,
            "customizations": customizations,
            "tile_audio": tile_audio,
            "frequent_words": frequent_words(owner),
            # A guardian setting up a child's board is not the child talking,
            # so their taps are not counted: the board gets no address to report them to.
            "managed": managed_child is not None,
            "increment_usage_url": None if managed_child else reverse('increment_word_usage'),
            "board_open_url": None if managed_child else reverse('record_board_open'),
            "frequent_words_url": None if managed_child else reverse('list_frequent_words'),
        },
    }
    return render(request, 'dashboard/board/board.html', context)
