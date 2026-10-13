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
import salitaaco.routes.feedback.feedback as feedback
import salitaaco.routes.institutions.institutions as institutions
import salitaaco.routes.overview.overview as overview
import salitaaco.routes.plan.plan as plan
import salitaaco.routes.privacy.privacy as privacy
import salitaaco.routes.reports.reports as reports
import salitaaco.routes.revenue.revenue as revenue
import salitaaco.routes.settings.settings as settings
import salitaaco.routes.subscriptions.subscriptions as subscriptions
import salitaaco.routes.support.support as support
import salitaaco.routes.system.access as system_access
import salitaaco.routes.system.general as system_general
import salitaaco.routes.technical_status.technical_status as technical_status
import salitaaco.routes.users.users as users
import salitaaco.routes.vocabulary.boards as admin_boards
import salitaaco.routes.vocabulary.words as words

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

    # A guardian's plan and payments. Frontend only for now: nothing is saved.
    path('plan/', plan.view_plan, name='plan'),
    path('plan/transactions/', plan.view_transactions, name='plan_transactions'),

    # ----- The admin's pages -----
    # The admin dashboard. Its address is from when it was the only admin page.
    path('analytics/', analytics.view_analytics, name='analytics'),
    path('reports/', reports.view_reports, name='reports'),
    path('reports/export/', reports.export_report, name='export_report'),

    path('users/', users.view_users, name='users'),
    path('users/<int:user_id>/status/', users.set_user_status, name='set_user_status'),

    # The boards and their words: the default vocabulary, and what admins change on top of it.
    path('vocabulary/boards/', admin_boards.view_admin_boards, name='admin_boards'),
    path('vocabulary/boards/status/', admin_boards.set_board_status, name='set_board_status'),
    path('vocabulary/words/', words.view_words, name='words'),
    path('vocabulary/words/<uuid:word_uuid>/', words.edit_word, name='edit_word'),
    path('vocabulary/words/<uuid:word_uuid>/delete/', words.delete_word, name='delete_word'),

    # Schools and centres. May be removed, with routes/institutions/.
    path('institutions/', institutions.view_institutions, name='institutions'),
    path('institutions/<uuid:institution_uuid>/', institutions.edit_institution, name='edit_institution'),
    path('institutions/<uuid:institution_uuid>/delete/', institutions.delete_institution, name='delete_institution'),

    # Ratings and support messages. May be removed, with routes/feedback/.
    path('feedback/', feedback.view_feedback, name='feedback'),
    path('feedback/messages/<uuid:message_uuid>/resolve/', feedback.resolve_support_message, name='resolve_support_message'),

    path('system/general/', system_general.view_general_settings, name='system_general'),
    path('system/access/', system_access.view_access_control, name='system_access'),
    path('system/access/<int:user_id>/remove/', system_access.remove_admin, name='remove_admin'),
    # May be removed, with routes/privacy/ and routes/technical_status/.
    path('system/privacy/', privacy.view_privacy, name='system_privacy'),
    path('system/status/', technical_status.view_technical_status, name='system_status'),

    # The admin's payments to approve and the plans. Frontend only for now: nothing is saved.
    path('revenue/', revenue.view_revenue, name='revenue'),
    path('subscriptions/', subscriptions.view_subscriptions, name='subscriptions'),
]
