from django.urls import path
from django.views.generic import RedirectView

import salitaaco.routes.account.account as account
import salitaaco.routes.analytics.analytics as analytics
import salitaaco.routes.board.board as board
import salitaaco.routes.board.customizations as customizations
import salitaaco.routes.board.usage as usage

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='board'), name='dashboard'),

    path('board/', board.view_board, name='board'),
    path('board/customizations/<str:customization_uuid>/image/', customizations.view_customization_image, name='view_customization_image'),
    path('board/customizations/<str:customization_uuid>/sound/', customizations.view_customization_sound, name='view_customization_sound'),
    path('board/customizations/reset/<str:customization_uuid>/', customizations.reset_customization, name='reset_customization'),
    path('board/usage/increment/', usage.increment_word_usage, name='increment_word_usage'),
    path('board/usage/frequent/', usage.list_frequent_words, name='list_frequent_words'),

    path('account/', account.manage_account, name='account'),
    path('account/avatar/', account.view_avatar, name='view_avatar'),
    path('account/avatar/remove/', account.remove_avatar, name='remove_avatar'),

    path('analytics/', analytics.view_analytics, name='analytics'),
]
