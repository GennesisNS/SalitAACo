from django.contrib import admin

from salitaaco.models.admin_account import AdminAccount
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.customization import Customization
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.rating import Rating
from salitaaco.models.word_usage import WordUsage

# The Django admin is off by default (SHOW_ADMIN_ROUTES). The back office is
# the admin dashboard at /dashboard/analytics/.


@admin.register(ChildAccount)
class ChildAccountAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "guardian", "age", "created_at")
    search_fields = ("display_name", "user__username", "guardian__display_name")


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
    list_display = ("word", "user", "has_image", "has_sound", "updated_at")
    search_fields = ("word", "user__username")


@admin.register(WordUsage)
class WordUsageAdmin(admin.ModelAdmin):
    list_display = ("word", "user", "use_count", "last_used")
    search_fields = ("word", "user__username")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "rating", "updated_at")
    search_fields = ("user__username", "comment")
