from django.urls import path
from django.views.generic import RedirectView

import salitaaco.routes.account.account as account
import salitaaco.routes.analytics.analytics as analytics
import salitaaco.routes.board.board as board
import salitaaco.routes.board.customizations as customizations
import salitaaco.routes.board.usage as usage
import salitaaco.routes.children.boards as child_boards
import salitaaco.routes.children.children as children
import salitaaco.routes.children.usage as child_usage
import salitaaco.routes.children.voice as child_voice
import salitaaco.routes.family_voices.family_voices as family_voices
import salitaaco.routes.favorites.favorites as favorites
import salitaaco.routes.overview.overview as overview
import salitaaco.routes.settings.settings as settings
import salitaaco.routes.support.support as support

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='board'), name='dashboard'),

    path('board/', board.view_board, name='board'),
    path('board/customizations/<uuid:customization_uuid>/image/', customizations.view_customization_image, name='view_customization_image'),
    path('board/customizations/<uuid:customization_uuid>/sound/', customizations.view_customization_sound, name='view_customization_sound'),
    path('board/customizations/reset/<uuid:customization_uuid>/', customizations.reset_customization, name='reset_customization'),
    path('board/usage/increment/', usage.increment_word_usage, name='increment_word_usage'),
    path('board/usage/board/', usage.record_board_open, name='record_board_open'),
    path('board/usage/frequent/', usage.list_frequent_words, name='list_frequent_words'),

    path('profile/', account.manage_account, name='profile'),
    path('profile/avatar/', account.view_avatar, name='view_avatar'),
    path('profile/avatar/remove/', account.remove_avatar, name='remove_avatar'),

    path('settings/', settings.view_settings, name='settings'),

    # A guardian's first page.
    path('overview/', overview.view_overview, name='overview'),

    # A guardian's children: their accounts, and their boards for setting up tiles.
    path('children/', children.view_children, name='children'),
    path('children/<uuid:child_uuid>/', children.manage_child, name='manage_child'),
    path('children/<uuid:child_uuid>/avatar/', children.view_child_avatar, name='view_child_avatar'),
    path('children/<uuid:child_uuid>/avatar/remove/', children.remove_child_avatar, name='remove_child_avatar'),
    path('children/<uuid:child_uuid>/board/', board.view_board, name='child_board'),
    # The pages about one child, reached from the sidebar for the selected child.
    path('children/<uuid:child_uuid>/boards/', child_boards.manage_child_boards, name='child_boards'),
    path('children/<uuid:child_uuid>/voice/', child_voice.choose_child_voice, name='child_voice'),
    path('children/<uuid:child_uuid>/usage/', child_usage.view_child_usage, name='child_usage'),

    # Words a guardian puts on a child's Paborito screen. May be removed, with routes/favorites/.
    path('children/<uuid:child_uuid>/favorites/', favorites.manage_favorites, name='favorites'),
    path('children/<uuid:child_uuid>/favorites/<uuid:favorite_uuid>/remove/', favorites.remove_favorite, name='remove_favorite'),

    # A guardian's family voices: cloned family members' voices the tiles are spoken in.
    path('family-voices/', family_voices.view_family_voices, name='family_voices'),
    path('family-voices/<uuid:family_voice_uuid>/generate/', family_voices.generate_family_voice, name='generate_family_voice'),
    path('family-voices/<uuid:family_voice_uuid>/delete/', family_voices.remove_family_voice, name='remove_family_voice'),
    path('family-voices/<uuid:family_voice_uuid>/words/<slug:word_slug>.mp3', family_voices.play_family_voice_word, name='play_family_voice_word'),

    path('support/', support.view_support, name='support'),

    path('analytics/', analytics.view_analytics, name='analytics'),
]
