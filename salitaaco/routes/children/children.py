import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import IntegerField, Sum
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.defaults.user_roles import CHILD
from salitaaco.forms.account.profile_information import ProfileInformationForm
from salitaaco.forms.account.upload_avatar import UploadAvatarForm
from salitaaco.forms.children.choose_family_voice import SHARED_VOICE, ChooseFamilyVoiceForm
from salitaaco.forms.children.create_child import CreateChildForm
from salitaaco.forms.children.delete_child import DeleteChildForm
from salitaaco.forms.children.reset_child_password import ResetChildPasswordForm
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.customization import Customization
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.utils.account import add_to_group, delete_user_account
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.analytics import bar_width
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_guardian, multi_user_test
from salitaaco.utils.uploads import random_upload_name
from salitaaco.utils.word_usage import frequent_words

logger = logging.getLogger(__name__)

CHILD_USAGE_WORDS = 20


@active_nav("children")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_children(request):
    guardian = get_object_or_404(GuardianAccount, user=request.user)

    create_child_form = CreateChildForm()

    if request.method == "POST":
        create_child_form = CreateChildForm(request.POST)
        if create_child_form.is_valid():
            with transaction.atomic():
                user = User.objects.create_user(
                    username=create_child_form.cleaned_data['username'],
                    password=create_child_form.cleaned_data['password'],
                )
                child = ChildAccount.objects.create(
                    user=user,
                    guardian=guardian,
                    display_name=create_child_form.cleaned_data['display_name'],
                    age=create_child_form.cleaned_data['age'],
                )
                add_to_group(user, CHILD)
            logger.info("Guardian %s created child account %s", request.user.username, user.username)
            messages.success(request, f"Nagawa na ang account ni {child.display_name}.")
            return redirect('children')

    children = guardian.children.select_related("user").annotate(
        total_taps=Coalesce(Sum("user__word_usages__use_count"), 0, output_field=IntegerField()),
    ).order_by("display_name")

    page_obj = paginate(children, request.GET.get("page", 1))

    context = {
        "create_child_form": create_child_form,
        "show_create_child_modal": bool(create_child_form.errors),
        "children": page_obj,
        "page_obj": page_obj,
    }
    return render(request, 'dashboard/children/children.html', context)


@active_nav("children")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def manage_child(request, child_uuid):
    child = get_object_or_404(ChildAccount, uuid=child_uuid, guardian__user=request.user)

    child_form = ProfileInformationForm(initial={
        "display_name": child.display_name,
        "age": child.age,
    })
    avatar_form = UploadAvatarForm()
    password_form = ResetChildPasswordForm()
    delete_child_form = DeleteChildForm(guardian_user=request.user)
    voice_form = ChooseFamilyVoiceForm(
        initial={"family_voice": str(child.family_voice.uuid) if child.family_voice else SHARED_VOICE},
        guardian=child.guardian,
    )

    if request.method == "POST":
        if "voice_form" in request.POST:
            voice_form = ChooseFamilyVoiceForm(request.POST, guardian=child.guardian)
            if voice_form.is_valid():
                chosen = voice_form.cleaned_data['family_voice']
                child.family_voice = child.guardian.family_voices.get(uuid=chosen) if chosen else None
                child.save()
                messages.success(request, f"Naka-save na ang boses na maririnig ni {child.display_name}.")
                return redirect('manage_child', child_uuid=child.uuid)

        if "child_form" in request.POST:
            child_form = ProfileInformationForm(request.POST)
            if child_form.is_valid():
                child.display_name = child_form.cleaned_data['display_name']
                child.age = child_form.cleaned_data['age']
                child.save()
                messages.success(request, "Naka-save na ang profile ng bata.")
                return redirect('manage_child', child_uuid=child.uuid)

        if "avatar_form" in request.POST:
            avatar_form = UploadAvatarForm(request.POST, request.FILES)
            if avatar_form.is_valid():
                avatar = avatar_form.cleaned_data['avatar']
                child.set_avatar(random_upload_name(avatar.content_type), avatar, avatar.content_type)
                messages.success(request, "Nai-save na ang larawan.")
                return redirect('manage_child', child_uuid=child.uuid)

        if "password_form" in request.POST:
            password_form = ResetChildPasswordForm(request.POST)
            if password_form.is_valid():
                # This also ends the child's open sessions; they log in again with the new password.
                child.user.set_password(password_form.cleaned_data['new_password'])
                child.user.save()
                messages.success(request, f"Nabago na ang password ni {child.display_name}.")
                return redirect('manage_child', child_uuid=child.uuid)

        if "delete_child_form" in request.POST:
            delete_child_form = DeleteChildForm(request.POST, guardian_user=request.user)
            if delete_child_form.is_valid():
                display_name = child.display_name
                delete_user_account(child.user)
                messages.success(request, f"Permanente nang nabura ang account ni {display_name}.")
                return redirect('children')

    usage = frequent_words(child.user, CHILD_USAGE_WORDS)
    highest = max((item["use_count"] for item in usage), default=0)
    for item in usage:
        item["width"] = bar_width(item["use_count"], highest)

    customizations = Customization.objects.filter(user=child.user)

    context = {
        "child": child,
        "child_form": child_form,
        "avatar_form": avatar_form,
        "password_form": password_form,
        "delete_child_form": delete_child_form,
        "show_delete_child_modal": bool(delete_child_form.errors),
        "voice_form": voice_form,
        "usage": usage,
        "total_taps": child.user.word_usages.aggregate(total=Sum("use_count"))["total"] or 0,
        "image_count": customizations.exclude(image="").count(),
        "sound_count": customizations.exclude(sound="").count(),
    }
    return render(request, 'dashboard/children/child.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_child_avatar(request, child_uuid):
    child = get_object_or_404(ChildAccount, uuid=child_uuid, guardian__user=request.user)
    if not child.has_avatar:
        raise Http404()
    response = FileResponse(child.avatar.open('rb'), content_type=child.avatar_mime or "application/octet-stream")
    response["Cache-Control"] = "private, max-age=86400"
    return response


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
@require_POST
def remove_child_avatar(request, child_uuid):
    child = get_object_or_404(ChildAccount, uuid=child_uuid, guardian__user=request.user)
    child.remove_avatar()
    messages.success(request, "Naalis na ang larawan.")
    return redirect('manage_child', child_uuid=child.uuid)
