import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from salitaaco.forms.system.general_settings import GeneralSettingsForm
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test

logger = logging.getLogger(__name__)

FIELDS = ["contact_email", "contact_phone", "maintenance_mode", "maintenance_message"]


@active_nav("system_general")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_general_settings(request):
    """System Settings > General: how to reach support, and maintenance mode."""
    setting = SiteSetting.load()

    settings_form = GeneralSettingsForm(initial={field: getattr(setting, field) for field in FIELDS})

    if request.method == "POST":
        settings_form = GeneralSettingsForm(request.POST)
        if settings_form.is_valid():
            was_in_maintenance = setting.maintenance_mode
            for field in FIELDS:
                setattr(setting, field, settings_form.cleaned_data[field])
            setting.save()
            if setting.maintenance_mode != was_in_maintenance:
                logger.warning("Admin %s turned maintenance mode %s", request.user.username,
                               "on" if setting.maintenance_mode else "off")
            messages.success(request, "Naka-save na ang mga setting.")
            return redirect('system_general')

    context = {
        "settings_form": settings_form,
        "setting": setting,
    }
    return render(request, 'dashboard/system/general.html', context)
