from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template.loader import render_to_string


def error_context(status_code, title, message):
    return {
        "status_code": status_code,
        "title": title,
        "message": message,
    }


def render_error(request, status_code, title, message):
    return render(request, 'http_error.html', error_context(status_code, title, message), status=status_code)


def bad_request(request, exception=None):
    return render_error(request, 400, "Hindi maintindihan ang request", "May mali sa ipinadalang request.")


def permission_denied(request, exception=None):
    return render_error(request, 403, "Access denied", "Walang pahintulot ang account na ito para sa pahinang ito.")


def page_not_found(request, exception=None):
    return render_error(request, 404, "Walang ganitong pahina", "Hindi mahanap ang pahinang hinahanap mo.")


def server_error(request):
    # Drawn without the request, so without the context processors, which read
    # the database for the sidebar and the account: the error may be the database.
    content = render_to_string('http_error.html', error_context(500, "May problema sa server", "Pakisubukan muli mamaya."))
    return HttpResponseServerError(content)
