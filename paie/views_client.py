from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from paie.models import PaieMois, Salarie, VariablePaie
from dossiers.models import NotificationPaie
from paie.forms import VariablePaieForm
from dossiers.notifications import envoyer_notifications_paie



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
        salaries = Salarie.objects.all().order_by("nom")
        return render(request, "paie/client/salaries.html", {"salaries": salaries})

    # CLIENT → accès limité
    client = request.user.client
    salaries = Salarie.objects.filter(client=client).order_by("nom")

    return render(request, "paie/client/salaries.html", {"salaries": salaries})

def client_fiche_salarie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)

    return render(request, "paie/client/salaries/fiche_salarie.html", {
        "salarie": salarie
    })


def client_salarie_remunerations(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)

    variables = VariablePaie.objects.filter(
        salarie=salarie
    ).select_related("paie_mois").order_by("-paie_mois__annee", "-paie_mois__mois")

    return render(request, "paie/client/salaries/remunerations.html", {
        "salarie": salarie,
        "variables": variables,
    })



# ----------------------------------------------------
#   VARIABLES
# ----------------------------------------------------

from datetime import date
from django.db import models
import calendar

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

    # --- LOGIQUE D'AFFICHAGE DU SALARIÉ DANS CE MOIS -----------------------

    # Début du mois (ex : 2026-06-01)
    date_debut_mois = date(mois.annee, mois.mois, 1)

    # Le salarié doit apparaître si :
    # - actif
    # - OU date_sortie NULL
    # - OU date_sortie >= début du mois
    if not (
        salarie.actif or
        salarie.date_sortie is None or
        salarie.date_sortie >= date_debut_mois
    ):
        # Le salarié est sorti avant ce mois → on bloque l'accès
        return render(request, "paie/client/salaries/salarie_non_disponible.html", {
            "mois": mois,
            "salarie": salarie,
        })

    # -----------------------------------------------------------------------

    # Si le mois est validé → pas de modification
    if mois.client_valide:
        return render(request, "paie/client/mois_verrouille.html", {"mois": mois})

    # Récupération ou création des variables
    variables, created = VariablePaie.objects.get_or_create(
        paie_mois=mois,
        salarie=salarie
    )

    # POST → mise à jour manuelle
    if request.method == "POST":
        variables.heures_sup_25 = request.POST.get("heures_sup_25", "")
        variables.conges_debut = request.POST.get("conges_debut", "")
        variables.absences_maladie = request.POST.get("absences_maladie", "")
        variables.absences_autres = request.POST.get("absences_autres", "")
        variables.primes = request.POST.get("primes", "")
        variables.acomptes = request.POST.get("acomptes", "")
        variables.autres_infos = request.POST.get("autres_infos", "")

        variables.save()

        return redirect("paie:client_mois_detail", mois_id=mois.id)

    # GET → on envoie les données au template
    return render(request, "paie/client/variables_salarie.html", {
        "mois": mois,
        "salarie": salarie,
        "variables": variables,
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

        # 🔔 Notification interne
        NotificationPaie.objects.create(
            client=mois.client,
            paie_mois=mois,
            lu_cabinet=False,
            lu_partenaire=False
        )

        return redirect("paie:client_mois_detail", mois_id=mois.id)

    # CLIENT → accès limité
    client = request.user.client
    mois = get_object_or_404(PaieMois, id=mois_id, client=client)

    mois.client_valide = True
    mois.date_validation_client = timezone.now()
    mois.save()

    # 🔔 Notification interne
    NotificationPaie.objects.create(
        client=mois.client,
        paie_mois=mois,
        lu_cabinet=False,
        lu_partenaire=False
    )

    # 📧 Envoi email (MANQUAIT ICI)
    envoyer_notifications_paie(mois)

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


from datetime import date
from django.db import models
import calendar

@login_required
def mois_detail(request, mois_id):

    # ADMIN → accès total
    if request.user.groups.filter(name="Utilisateur").exists():
        mois = get_object_or_404(PaieMois, id=mois_id)
        client = mois.client
    else:
        # CLIENT → accès limité
        client = request.user.client
        mois = get_object_or_404(PaieMois, id=mois_id, client=client)

    # --- LOGIQUE D'AFFICHAGE DES SALARIÉS POUR CE MOIS ---------------------

    # Début du mois (ex : 2026-06-01)
    date_debut_mois = date(mois.annee, mois.mois, 1)

    # Filtre identique à celui utilisé dans variables_paie_salaries
    salaries = Salarie.objects.filter(
        client=client
    ).filter(
        models.Q(actif=True) |
        models.Q(date_sortie__isnull=True) |
        models.Q(date_sortie__gte=date_debut_mois)
    ).order_by("nom")

    # -----------------------------------------------------------------------

    # Récupération de toutes les variables du mois
    variables = VariablePaie.objects.filter(paie_mois=mois)

    # Dictionnaire : { salarie_id : VariablePaie }
    variables_dict = {v.salarie_id: v for v in variables}

    return render(request, "paie/client/mois_detail.html", {
        "mois": mois,
        "salaries": salaries,
        "variables_dict": variables_dict,
    })



@login_required
def client_liste_mois(request):
    client = request.user.client
    mois_list = PaieMois.objects.filter(client=client).order_by('-annee', '-mois')

    return render(request, "paie/client/liste_mois_client.html", {
        "mois_list": mois_list,
        "client": client,
    })

