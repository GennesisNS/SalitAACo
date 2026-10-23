import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.defaults.user_roles import CHILD
from salitaaco.forms.account.profile_information import ProfileInformationForm
from salitaaco.forms.account.upload_avatar import UploadAvatarForm
from salitaaco.forms.children.create_child import CreateChildForm
from salitaaco.forms.children.delete_child import DeleteChildForm
from salitaaco.forms.children.reset_child_password import ResetChildPasswordForm
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.customization import Customization
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.utils.account import add_to_group, delete_user_account
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.children import add_board_numbers, children_with_numbers, guardian_child_or_404
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_guardian, multi_user_test
from salitaaco.utils.plans import child_slots
from salitaaco.utils.uploads import random_upload_name

logger = logging.getLogger(__name__)


@active_nav("children")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_children(request):
    guardian = get_object_or_404(GuardianAccount, user=request.user)
    # How many children the guardian's plan allows; over it, no more are made.
    slots = child_slots(guardian)

    create_child_form = CreateChildForm()

    if request.method == "POST":
        if not slots["can_add"]:
            messages.error(request, slots["message"])
            return redirect('children')

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

    page_obj = paginate(children_with_numbers(guardian.children.all()), request.GET.get("page", 1))
    page_obj.object_list = add_board_numbers(list(page_obj.object_list))

    context = {
        "create_child_form": create_child_form,
        "child_slots": slots,
        # ?add=1 is how the overview's "add a child" button opens the form straight away.
        "show_create_child_modal": slots["can_add"] and (bool(create_child_form.errors) or "add" in request.GET),
        "children": page_obj,
        "page_obj": page_obj,
    }
    return render(request, 'dashboard/children/children.html', context)


@active_nav("children")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def manage_child(request, child_uuid):
    child = guardian_child_or_404(request, child_uuid)

    child_form = ProfileInformationForm(initial={
        "display_name": child.display_name,
        "age": child.age,
    })
    avatar_form = UploadAvatarForm()
    password_form = ResetChildPasswordForm()
    delete_child_form = DeleteChildForm(guardian_user=request.user)

    if request.method == "POST":
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

    customizations = Customization.objects.filter(user=child.user)

    context = {
        "child": child,
        "child_form": child_form,
        "avatar_form": avatar_form,
        "password_form": password_form,
        "delete_child_form": delete_child_form,
        "show_delete_child_modal": bool(delete_child_form.errors),
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
