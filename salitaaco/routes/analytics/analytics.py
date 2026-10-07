from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Exists, IntegerField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render

from salitaaco.backends.Search import SearchModel
from salitaaco.backends.Sort import QuerysetSorter
from salitaaco.defaults.administrator_roles import ADMINISTRATOR
from salitaaco.forms.analytics.search_user import SearchUserForm
from salitaaco.models.rating import Rating
from salitaaco.models.word_usage import WordUsage
from salitaaco.utils import analytics
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_administrator, multi_user_test


@active_nav("analytics")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_analytics(request):
    search_user_form = SearchUserForm(request.GET or None)

    users = SearchModel(
        User, request.GET.get("query", ""), fields_to_look=["username", "profile__display_name"],
    ).search()

    users = users.select_related("profile").annotate(
        image_count=Count("customizations", filter=Q(customizations__image__gt=""), distinct=True),
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
        is_admin=Exists(User.groups.through.objects.filter(user_id=OuterRef("pk"), group__name=ADMINISTRATOR)),
    )

    users = QuerysetSorter(
        queryset=users,
        order_by=request.GET.get("order_by", ""),
        allowed_fields={"username": "username", "date_joined": "date_joined", "last_login": "last_login"},
        default="-date_joined",
    ).sort()

    users_page = paginate(users, request.GET.get("users_page", 1))

    ratings = Rating.objects.select_related("user__profile").order_by("-updated_at")
    ratings_page = paginate(ratings, request.GET.get("ratings_page", 1))

    overview = analytics.overview()

    context = {
        "overview": overview,
        "stat_cards": analytics.stat_cards(overview),
        "signups": analytics.signups_by_day(),
        "rating_distribution": analytics.rating_distribution(),
        "top_words": analytics.top_words(),
        "search_user_form": search_user_form,
        "users": users_page,
        "ratings": ratings_page,
    }
    return render(request, 'dashboard/analytics/analytics.html', context)
