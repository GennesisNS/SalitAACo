import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from salitaaco.forms.system.general_settings import GeneralSettingsForm
from salitaaco.forms.system.payment_settings import PaymentSettingsForm
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test
from salitaaco.utils.uploads import random_upload_name

logger = logging.getLogger(__name__)

FIELDS = ["contact_email", "contact_phone", "maintenance_mode", "maintenance_message"]
PAYMENT_FIELDS = ["gcash_name", "gcash_number"]


@active_nav("system_general")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_general_settings(request):
    """
    System Settings > General: how to reach support, maintenance mode, and
    where guardians pay. The plans' limits are on Mga Plano (routes/system/plans.py).
    """
    setting = SiteSetting.load()

    settings_form = GeneralSettingsForm(initial={field: getattr(setting, field) for field in FIELDS})
    payment_form = PaymentSettingsForm(initial={field: getattr(setting, field) for field in PAYMENT_FIELDS})

    if request.method == "POST":
        if "payment_form" in request.POST:
            payment_form = PaymentSettingsForm(request.POST, request.FILES)
            if payment_form.is_valid():
                for field in PAYMENT_FIELDS:
                    setattr(setting, field, payment_form.cleaned_data[field])
                qr = payment_form.cleaned_data["gcash_qr"]
                if qr:
                    setting.set_gcash_qr(random_upload_name(qr.content_type), qr, qr.content_type)
                    logger.info("Admin %s replaced the GCash QR code", request.user.username)
                else:
                    setting.save()
                messages.success(request, "Naka-save na ang bayaran sa GCash.")
                return redirect('system_general')

        elif "remove_gcash_qr" in request.POST:
            setting.remove_gcash_qr()
            logger.info("Admin %s removed the GCash QR code", request.user.username)
            messages.success(request, "Naalis na ang QR code. Hindi muna makakabayad ang mga tagapag-alaga.")
            return redirect('system_general')

        # The first form of the page, and what a post without a button's name is.
        else:
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
        "payment_form": payment_form,
        "setting": setting,
    }
    return render(request, 'dashboard/system/general.html', context)
