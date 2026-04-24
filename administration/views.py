from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import UserAddForm, UserEditForm
from dossiers.models import EmailLog


# Vérification : accès réservé au staff ou superuser
def admin_required(user):
    return user.is_superuser


def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, "administration/admin_dashboard.html")

def is_superadmin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superadmin)
def email_logs_list(request):
    logs = EmailLog.objects.order_by("-date_envoi")
    return render(request, "administration/email_logs_list.html", {"logs": logs})


@user_passes_test(admin_required)
def users_list(request):
    users = User.objects.all().order_by("username")
    return render(request, "administration/users_list.html", {"users": users})


@user_passes_test(admin_required)
def user_add(request):
    if request.method == "POST":
        form = UserAddForm(request.POST)

        if form.is_valid():

            # Sécurité : empêcher un staff de créer un superuser
            if not request.user.is_superuser and form.cleaned_data.get("is_superuser"):
                messages.error(request, "Vous ne pouvez pas créer un superutilisateur.")
                return redirect("admin_users_list")

            # Création de l'utilisateur
            form.save()
            messages.success(request, "Utilisateur créé avec succès.")
            return redirect("admin_users_list")

    else:
        form = UserAddForm()

    return render(request, "administration/user_add.html", {"form": form})


@user_passes_test(admin_required)
def user_edit(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user_obj)

        if form.is_valid():

            # Sécurité : un staff ne peut PAS rendre quelqu’un superuser
            if not request.user.is_superuser and form.cleaned_data.get("is_superuser"):
                messages.error(request, "Vous ne pouvez pas attribuer le statut superutilisateur.")
                return redirect("admin_users_list")

            form.save()
            messages.success(request, "Utilisateur mis à jour.")
            return redirect("admin_users_list")

    else:
        form = UserEditForm(instance=user_obj)

    return render(request, "administration/user_edit.html", {
        "form": form,
        "user": user_obj
    })

@user_passes_test(admin_required)
def user_toggle_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, "Statut du compte mis à jour.")
    return redirect("admin_users_list")

@user_passes_test(admin_required)
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Sécurité : empêcher la suppression du superuser
    if user.is_superuser:
        messages.error(request, "Impossible de supprimer un superutilisateur.")
        return redirect("admin_users_list")

    # Optionnel : empêcher un staff de supprimer un autre staff
    if user.is_staff and not request.user.is_superuser:
        messages.error(request, "Vous ne pouvez pas supprimer un utilisateur staff.")
        return redirect("admin_users_list")

    user.delete()
    messages.success(request, "Utilisateur supprimé avec succès.")
    return redirect("admin_users_list")


from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

def admin_required(user):
    return user.is_superuser


@user_passes_test(admin_required)
def groups_list(request):
    groups = Group.objects.all().order_by("name")
    return render(request, "administration/groups_list.html", {"groups": groups})


@user_passes_test(admin_required)
def group_edit(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    permissions = Permission.objects.all()

    if request.method == "POST":
        group.name = request.POST.get("name")
        perms = request.POST.getlist("permissions")
        group.permissions.set(perms)
        group.save()

        messages.success(request, "Groupe mis à jour.")
        return redirect("admin_groups_list")

    return render(request, "administration/group_edit.html", {
        "group": group,
        "permissions": permissions,
    })

def access_denied(request):
    return render(request, "administration/access_denied.html")

