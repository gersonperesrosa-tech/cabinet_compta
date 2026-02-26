from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from paie.models import PaieMois, Salarie, VariablePaie
from paie.forms import VariablePaieForm




@login_required
def paie_client_dashboard(request):
    client = request.user.client

    mois_en_cours = (
        PaieMois.objects
        .filter(client=client)
        .order_by("-annee", "-mois")
        .first()
    )

    derniers_mois = (
        PaieMois.objects
        .filter(client=client)
        .order_by("-annee", "-mois")[:3]
    )

    salaries = Salarie.objects.filter(client=client)
    nb_salaries = salaries.count()
    nb_actifs = salaries.filter(actif=True).count()
    nb_inactifs = nb_salaries - nb_actifs

    variables_remplies = 0
    total_variables = 0

    if mois_en_cours:
        total_variables = VariablePaie.objects.filter(paie_mois=mois_en_cours).count()
        variables_remplies = VariablePaie.objects.filter(
            paie_mois=mois_en_cours
        ).exclude(
            heures_sup_25="",
            heures_sup_50="",
            primes="",
            conges_debut="",
            conges_fin="",
            absences_maladie="",
            absences_autres="",
            acomptes="",
            autres_infos=""
        ).count()

    context = {
        "client": client,  # ← ICI
        "mois_en_cours": mois_en_cours,
        "derniers_mois": derniers_mois,
        "nb_salaries": nb_salaries,
        "nb_actifs": nb_actifs,
        "nb_inactifs": nb_inactifs,
        "variables_remplies": variables_remplies,
        "total_variables": total_variables,
    }

    return render(request, "paie/client/dashboard.html", context)

# ----------------------------------------------------
#   SALARIES
# ----------------------------------------------------


@login_required
def liste_salaries(request):

    # ADMIN → accès total
    if request.user.groups.filter(name="Utilisateur").exists():
        salaries = Salarie.objects.all()
        return render(request, "paie/client/salaries.html", {"salaries": salaries})

    # CLIENT → accès limité
    client = request.user.client
    salaries = Salarie.objects.filter(client=client)

    return render(request, "paie/client/salaries.html", {"salaries": salaries})

# ----------------------------------------------------
#   VARIABLES
# ----------------------------------------------------

@login_required
def variables_salarie(request, mois_id, salarie_id):

    # ADMIN → accès total
    if request.user.groups.filter(name="Utilisateur").exists():
        mois = get_object_or_404(PaieMois, id=mois_id)
        salarie = get_object_or_404(Salarie, id=salarie_id)
    else:
        # CLIENT → accès limité
        client = request.user.client
        mois = get_object_or_404(PaieMois, id=mois_id, client=client)
        salarie = get_object_or_404(Salarie, id=salarie_id, client=client)

    # Si le mois est validé → pas de modification
    if mois.client_valide:
        return render(request, "paie/client/mois_verrouille.html", {"mois": mois})

    variables, created = VariablePaie.objects.get_or_create(
        paie_mois=mois,
        salarie=salarie
    )

    if request.method == "POST":
        form = VariablePaieForm(request.POST, instance=variables)
        if form.is_valid():
            form.save()
            return redirect("paie:client_mois_detail", mois_id=mois.id)

    else:
        form = VariablePaieForm(instance=variables)

    return render(request, "paie/client/variables_salarie.html", {
        "form": form,
        "mois": mois,
        "salarie": salarie,
    })

# ----------------------------------------------------
#   MOIS
# ----------------------------------------------------


from django.utils import timezone

@login_required
def valider_mois(request, mois_id):

    # ADMIN → accès total
    if request.user.groups.filter(name="Utilisateur").exists():
        mois = get_object_or_404(PaieMois, id=mois_id)
        mois.client_valide = True
        mois.date_validation_client = timezone.now()
        mois.save()
        return redirect("paie:client_mois_detail", mois_id=mois.id)

    # CLIENT → accès limité
    client = request.user.client
    mois = get_object_or_404(PaieMois, id=mois_id, client=client)

    mois.client_valide = True
    mois.date_validation_client = timezone.now()
    mois.save()

    return redirect("paie:client_mois_detail", mois_id=mois.id)

@login_required
def creer_mois_suivant(request):
    client = request.user.client

    # On récupère le dernier mois existant
    dernier = PaieMois.objects.filter(client=client).order_by("-annee", "-mois").first()

    if not dernier:
        # Aucun mois → on crée le premier
        nouveau_mois = 1
        nouvelle_annee = timezone.now().year
    else:
        # Calcul du mois suivant
        if dernier.mois == 12:
            nouveau_mois = 1
            nouvelle_annee = dernier.annee + 1
        else:
            nouveau_mois = dernier.mois + 1
            nouvelle_annee = dernier.annee

    # Création du mois
    PaieMois.objects.create(
        client=client,
        mois=nouveau_mois,
        annee=nouvelle_annee
    )

    return redirect("paie:client_liste_mois")


@login_required
def mois_detail(request, mois_id):

    # ADMIN → accès total
    if request.user.groups.filter(name="Utilisateur").exists():
        mois = get_object_or_404(PaieMois, id=mois_id)
        salaries = Salarie.objects.filter(client=mois.client)
        return render(request, "paie/client/mois_detail.html", {
            "mois": mois,
            "salaries": salaries,
        })

    # CLIENT → accès limité
    client = request.user.client
    mois = get_object_or_404(PaieMois, id=mois_id, client=client)
    salaries = Salarie.objects.filter(client=client)

    return render(request, "paie/client/mois_detail.html", {
        "mois": mois,
        "salaries": salaries,
    })


@login_required
def client_liste_mois(request):
    client = request.user.client
    mois_list = PaieMois.objects.filter(client=client).order_by('-annee', '-mois')

    return render(request, "paie/client/liste_mois_client.html", {
        "mois_list": mois_list,
        "client": client,
    })

