from django import template

from salitaaco.models.rating import Rating

register = template.Library()


@register.filter
def stars(value):
    """3 -> '★★★☆☆'"""
    filled = max(0, min(int(value or 0), Rating.MAX_RATING))
    return "★" * filled + "☆" * (Rating.MAX_RATING - filled)
