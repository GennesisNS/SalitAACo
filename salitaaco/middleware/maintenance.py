from django.conf import settings
from django.shortcuts import render
from django.urls import reverse

from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.perms_check import is_administrator


class MaintenanceModeMiddleware:
    """
    While maintenance mode is on (System Settings > General), everyone but
    admins gets the maintenance page instead of the app. Logging in and out
    stay open, so that an admin can get in to turn it off.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self.is_closed_to(request):
            setting = SiteSetting.load()
            context = {"message": setting.maintenance_message}
            # 503 with Retry-After tells browsers and search engines this is temporary.
            response = render(request, 'maintenance.html', context, status=503)
            response["Retry-After"] = "3600"
            # Django logs every 5xx answer as an error. This one is on purpose, and
            # one line per visitor would bury the real errors on Technical status.
            response._has_been_logged = True
            return response
        return self.get_response(request)

    def is_closed_to(self, request):
        if request.path.startswith((settings.STATIC_URL, "/admin")):
            return False
        if request.path in (reverse("login"), reverse("logout")):
            return False
        if not SiteSetting.objects.filter(pk=SiteSetting.ONLY_ROW, maintenance_mode=True).exists():
            return False
        return not (request.user.is_authenticated and is_administrator(request.user))
