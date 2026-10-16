"""
The "Mga Paaralan at Institusyon" page: the admin's record of the schools and
centres that use the app under an arrangement.

This page may be removed. Everything of it is here and in forms/institutions/,
models/institution.py (migration 0016), templates/dashboard/institutions/,
tests/institutions/, its three addresses in routes/dashboard/__init__.py and
its item in defaults/navigations.py. Nothing else uses any of it.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.forms.institutions.institution import InstitutionForm
from salitaaco.models.institution import Institution
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_administrator, multi_user_test

FIELDS = ["name", "contact_person", "contact_details", "seats", "plan_notes", "renewal_date", "is_active"]


@active_nav("institutions")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_institutions(request):
    institution_form = InstitutionForm()

    if request.method == "POST":
        institution_form = InstitutionForm(request.POST)
        if institution_form.is_valid():
            institution = Institution.objects.create(**{field: institution_form.cleaned_data[field] for field in FIELDS})
            messages.success(request, f"Naidagdag na ang {institution.name}.")
            return redirect('institutions')

    institutions = Institution.objects.order_by("name", "institution_id")

    context = {
        "institution_form": institution_form,
        "show_add_institution_modal": bool(institution_form.errors),
        "institutions": paginate(institutions, request.GET.get("page", 1)),
        "active_count": institutions.filter(is_active=True).count(),
        "total_count": institutions.count(),
    }
    return render(request, 'dashboard/institutions/institutions.html', context)


@active_nav("institutions")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def edit_institution(request, institution_uuid):
    institution = get_object_or_404(Institution, uuid=institution_uuid)

    institution_form = InstitutionForm(initial={field: getattr(institution, field) for field in FIELDS})

    if request.method == "POST":
        institution_form = InstitutionForm(request.POST)
        if institution_form.is_valid():
            for field in FIELDS:
                setattr(institution, field, institution_form.cleaned_data[field])
            institution.save()
            messages.success(request, f"Naka-save na ang {institution.name}.")
            return redirect('institutions')

    context = {
        "institution": institution,
        "institution_form": institution_form,
    }
    return render(request, 'dashboard/institutions/institution.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_administrator)
@require_POST
def delete_institution(request, institution_uuid):
    institution = get_object_or_404(Institution, uuid=institution_uuid)
    name = institution.name
    institution.delete()
    messages.success(request, f"Nabura na ang {name}.")
    return redirect('institutions')
