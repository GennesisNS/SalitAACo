from django.shortcuts import render


def render_error(request, status_code, title, message):
    context = {
        "status_code": status_code,
        "title": title,
        "message": message,
    }
    return render(request, 'http_error.html', context, status=status_code)


def bad_request(request, exception=None):
    return render_error(request, 400, "Hindi maintindihan ang request", "May mali sa ipinadalang request.")


def permission_denied(request, exception=None):
    return render_error(request, 403, "Access denied", "Walang pahintulot ang account na ito para sa pahinang ito.")


def page_not_found(request, exception=None):
    return render_error(request, 404, "Walang ganitong pahina", "Hindi mahanap ang pahinang hinahanap mo.")


def server_error(request):
    return render_error(request, 500, "May problema sa server", "Pakisubukan muli mamaya.")
