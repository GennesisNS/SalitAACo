from django.urls import path
from django.views.generic import RedirectView

import salitaaco.routes.account.account as account
import salitaaco.routes.analytics.analytics as analytics
import salitaaco.routes.board.board as board
import salitaaco.routes.board.customizations as customizations
import salitaaco.routes.board.usage as usage
import salitaaco.routes.children.children as children
import salitaaco.routes.settings.settings as settings

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='board'), name='dashboard'),

    path('board/', board.view_board, name='board'),
    path('board/customizations/<uuid:customization_uuid>/image/', customizations.view_customization_image, name='view_customization_image'),
    path('board/customizations/<uuid:customization_uuid>/sound/', customizations.view_customization_sound, name='view_customization_sound'),
    path('board/customizations/reset/<uuid:customization_uuid>/', customizations.reset_customization, name='reset_customization'),
    path('board/usage/increment/', usage.increment_word_usage, name='increment_word_usage'),
    path('board/usage/frequent/', usage.list_frequent_words, name='list_frequent_words'),

    path('profile/', account.manage_account, name='profile'),
    path('profile/avatar/', account.view_avatar, name='view_avatar'),
    path('profile/avatar/remove/', account.remove_avatar, name='remove_avatar'),

    path('settings/', settings.view_settings, name='settings'),

    # A guardian's children: their accounts, and their boards for setting up tiles.
    path('children/', children.view_children, name='children'),
    path('children/<uuid:child_uuid>/', children.manage_child, name='manage_child'),
    path('children/<uuid:child_uuid>/avatar/', children.view_child_avatar, name='view_child_avatar'),
    path('children/<uuid:child_uuid>/avatar/remove/', children.remove_child_avatar, name='remove_child_avatar'),
    path('children/<uuid:child_uuid>/board/', board.view_board, name='child_board'),

    path('analytics/', analytics.view_analytics, name='analytics'),
]
