from django.apps import AppConfig


class PublicConfig(AppConfig):
    """
    The public website: the one page at "/" that people see before they have an
    account. Its views, URLs, templates, CSS and JavaScript are all in this
    folder; the project only lists the app and includes its URLs.
    """
    name = "public"
