from django import template

register = template.Library()


@register.filter
def format_bytes(value):
    """1536 -> '1.5 KB'"""
    size = int(value or 0)
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
