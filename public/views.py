from django.shortcuts import redirect, render
from django.utils import timezone

from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.account import get_user_account, home_route
from salitaaco.utils.plans import offered_plans


def view_home(request):
    """
    The public website. Someone who is logged in has no use for it: they go
    straight to their own first page, as the site's root always sent them.
    """
    if request.user.is_authenticated:
        return redirect(home_route(get_user_account(request.user)))

    context = {
        # The same plans the admin sees on Mga Subscription and guardians on Plano at Subscription.
        "plans": [{**plan, "is_free": plan["price"] == 0} for plan in offered_plans()],
        # The support email and telephone an admin set on System Settings > General.
        "site_setting": SiteSetting.load(),
        "year": timezone.localdate().year,
    }
    return render(request, 'public/home.html', context)
