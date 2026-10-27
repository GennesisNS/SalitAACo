from django.contrib import admin

from salitaaco.models.added_word import AddedWord
from salitaaco.models.admin_account import AdminAccount
from salitaaco.models.board_status import BoardStatus
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.customization import Customization
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.generated_report import GeneratedReport
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.guardian_board import GuardianBoard
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan
from salitaaco.models.rating import Rating
from salitaaco.models.site_setting import SiteSetting
from salitaaco.models.support_message import SupportMessage
from salitaaco.models.word_usage import WordUsage

# Every model of the app is here (tests/admin_site/ checks that none is
# missing). The Django admin is off by default (SHOW_ADMIN_ROUTES); the back
# office is the admin dashboard at /dashboard/analytics/, which keeps the
# app's rules that a change made here skips.


@admin.register(ChildAccount)
class ChildAccountAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "guardian", "age", "created_at")
    search_fields = ("display_name", "user__username", "guardian__display_name")


@admin.register(FamilyVoice)
class FamilyVoiceAdmin(admin.ModelAdmin):
    list_display = ("name", "guardian", "consent_at", "consent_version", "created_at")
    search_fields = ("name", "guardian__display_name", "guardian__user__username")
    readonly_fields = ("elevenlabs_voice_id", "consent_at", "consent_version")


@admin.register(GuardianAccount)
class GuardianAccountAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "created_at")
    search_fields = ("display_name", "user__username")


@admin.register(AdminAccount)
class AdminAccountAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "created_at")
    search_fields = ("display_name", "user__username")


@admin.register(Customization)
class CustomizationAdmin(admin.ModelAdmin):
    list_display = ("word", "user", "has_sound", "updated_at")
    search_fields = ("word", "user__username")


@admin.register(WordUsage)
class WordUsageAdmin(admin.ModelAdmin):
    list_display = ("word", "user", "use_count", "last_used")
    search_fields = ("word", "user__username")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "rating", "updated_at")
    search_fields = ("user__username", "comment")


@admin.register(DailyUsage)
class DailyUsageAdmin(admin.ModelAdmin):
    list_display = ("day", "user", "kind", "name", "use_count")
    list_filter = ("kind",)
    search_fields = ("name", "user__username")
    date_hierarchy = "day"


@admin.register(HiddenBoard)
class HiddenBoardAdmin(admin.ModelAdmin):
    list_display = ("board", "child", "created_at")
    search_fields = ("board", "child__display_name", "child__user__username")


@admin.register(BoardStatus)
class BoardStatusAdmin(admin.ModelAdmin):
    list_display = ("board", "is_published", "updated_at")
    list_filter = ("is_published",)


@admin.register(AddedWord)
class AddedWordAdmin(admin.ModelAdmin):
    list_display = ("word", "board", "emoji", "has_icon_image", "created_at")
    list_filter = ("board",)
    search_fields = ("word",)


@admin.register(GuardianBoard)
class GuardianBoardAdmin(admin.ModelAdmin):
    list_display = ("name", "guardian", "emoji", "has_icon_image", "created_at")
    search_fields = ("name", "guardian__display_name", "guardian__user__username")


@admin.register(GuardianWord)
class GuardianWordAdmin(admin.ModelAdmin):
    list_display = ("word", "board", "guardian", "emoji", "has_icon_image", "created_at")
    search_fields = ("word", "board", "guardian__display_name", "guardian__user__username")


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ("guardian", "child", "created_at", "resolved_at")
    list_filter = ("resolved_at",)
    search_fields = ("message", "guardian__display_name", "guardian__user__username")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "price", "child_limit", "family_voice_limit", "offered", "position")
    list_editable = ("offered", "position")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("guardian", "plan", "amount", "status", "created_at", "reviewed_by", "starts_at", "ends_at")
    list_filter = ("status", "plan")
    search_fields = ("guardian__display_name", "guardian__user__username", "note")
    date_hierarchy = "created_at"


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ("report_id", "report_type", "file_type", "start_date", "end_date", "generated_by", "created_at")
    list_filter = ("report_type", "file_type")


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """The site has one row of settings (SiteSetting.load()): it is changed, never added to or deleted."""
    list_display = ("__str__", "maintenance_mode", "contact_email", "updated_at")

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
