import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from salitaaco.backends.Search import SearchModel
from salitaaco.backends.Sort import QuerysetSorter
from salitaaco.forms.analytics.search_user import SearchUserForm
from salitaaco.forms.users.set_user_status import SetUserStatusForm
from salitaaco.forms.users.user_status import ACTIVE, ALL, INACTIVE, UserStatusForm
from salitaaco.models.rating import Rating
from salitaaco.models.word_usage import WordUsage
from salitaaco.utils.account import ACCOUNT_RELATIONS, find_user_account
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_administrator, multi_user_test

logger = logging.getLogger(__name__)


@active_nav("users")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_users(request):
    """Every account, to search, sort, and filter by whether it is active."""
    search_user_form = SearchUserForm(request.GET or None)
    status_form = UserStatusForm(request.GET or None)
    status = status_form.chosen()

    found = SearchModel(
        User,
        request.GET.get("query", ""),
        fields_to_look=["username"] + [f"{relation}__display_name" for relation in ACCOUNT_RELATIONS],
    ).search()

    users = found
    if status == ACTIVE:
        users = users.filter(is_active=True)
    elif status == INACTIVE:
        users = users.filter(is_active=False)

    users = users.select_related(*ACCOUNT_RELATIONS).annotate(
        sound_count=Count("customizations", filter=Q(customizations__sound__gt=""), distinct=True),
        total_taps=Coalesce(
            Subquery(
                WordUsage.objects.filter(user=OuterRef("pk"))
                .values("user")
                .annotate(total=Sum("use_count"))
                .values("total")
            ),
            0,
            output_field=IntegerField(),
        ),
        rating_stars=Subquery(Rating.objects.filter(user=OuterRef("pk")).values("rating")),
    )

    users = QuerysetSorter(
        queryset=users,
        order_by=request.GET.get("order_by", ""),
        allowed_fields={"username": "username", "date_joined": "date_joined", "last_login": "last_login"},
        default="-date_joined",
    ).sort()

    users_page = paginate(users, request.GET.get("users_page", 1))

    # The account behind each row tells the template its name, age and kind.
    for user in users_page:
        user.account = find_user_account(user)

    counts = {
        ALL: found.count(),
        ACTIVE: found.filter(is_active=True).count(),
        INACTIVE: found.filter(is_active=False).count(),
    }

    context = {
        "search_user_form": search_user_form,
        "status": status,
        "tabs": [
            {"value": value, "label": label, "count": counts[value], "active": value == status}
            for value, label in status_form.fields["status"].choices
        ],
        "users": users_page,
    }
    return render(request, 'dashboard/users/users.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_administrator)
@require_POST
def set_user_status(request, user_id):
    """
    Make an account active or inactive. An inactive account cannot log in, and
    is logged out where it is logged in. Its data, and the accounts of a
    guardian's children, are left as they are.
    """
    user = get_object_or_404(User, pk=user_id)
    status_form = SetUserStatusForm(request.POST, acting_user=request.user, target_user=user)

    if status_form.is_valid():
        user.is_active = status_form.cleaned_data['active']
        user.save()
        logger.info("Admin %s made account %s %s", request.user.username, user.username,
                    "active" if user.is_active else "inactive")
        if user.is_active:
            messages.success(request, f"Aktibo na muli ang account na @{user.username}.")
        else:
            messages.success(request, f"Hindi na aktibo ang account na @{user.username}. Hindi na ito makakapag-log in.")
    else:
        messages.error(request, status_form.non_field_errors()[0])

    # Back to the list as it was: the same tab, search and page.
    back = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(back, allowed_hosts={request.get_host()}):
        return redirect(back)
    return redirect('users')
