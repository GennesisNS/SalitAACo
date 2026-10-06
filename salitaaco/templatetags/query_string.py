from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_replace(context, key, value):
    """
    The current query string with one parameter replaced, for page links that
    must keep the search and sort parameters: {% query_replace "users_page" 2 %}
    """
    query = context["request"].GET.copy()
    query[key] = value
    return "?" + query.urlencode()
