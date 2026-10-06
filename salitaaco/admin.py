from django.contrib import admin

from salitaaco.models.customization import Customization
from salitaaco.models.profile import Profile
from salitaaco.models.rating import Rating
from salitaaco.models.word_usage import WordUsage

# The Django admin is off by default (SHOW_ADMIN_ROUTES). The back office is
# the admin dashboard at /dashboard/analytics/.


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "age", "created_at")
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
