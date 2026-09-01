from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages

from .models import Client, Salarie, PaieMois, VariablePaie
from .forms import VariablePaieForm
from dossiers.notifications import envoyer_notifications_bs_verifie
from dossiers.audit import audit



def dashboard_cabinet(request):
    return render(request, "paie/cabinet/dashboard.html")

# ----------------------------------------------------
#   SALARIÉS (Gestion côté cabinet)
# ----------------------------------------------------

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from dossiers.models import Client
from .models import Salarie
from .forms import SalarieForm


@login_required
def liste_salaries_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    salaries = client.salaries.all().order_by("nom")

    # ⭐ AUDIT
    audit(
        client=client,
        user=request.user,
        action=f"Cabinet : consultation de la liste des salariés du client {client.nom}",
        metadata={"client_id": client.id}
    )

    return render(request, "paie/salaries/liste.html", {
        "client": client,
        "salaries": salaries,
    })



@login_required
def creer_salarie(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == "POST":
        form = SalarieForm(request.POST)
        if form.is_valid():
            salarie = form.save(commit=False)
            salarie.client = client
            salarie.save()

            # ⭐ AUDIT
            audit(
                client=client,
                user=request.user,
                action=f"Cabinet : création du salarié {salarie.nom}",
                metadata={"salarie_id": salarie.id}
            )

            return redirect("paie:cabinet_liste_salaries_client", client_id=client.id)
    else:
        form = SalarieForm()

    return render(request, "paie/salaries/creer.html", {
        "client": client,
        "form": form,
    })



@login_required
def modifier_salarie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)
    client = salarie.client

    if request.method == "POST":
        form = SalarieForm(request.POST, instance=salarie)
        if form.is_valid():
            form.save()

            # ⭐ AUDIT
            audit(
                client=client,
                user=request.user,
                action=f"Cabinet : modification du salarié {salarie.nom}",
                metadata={"salarie_id": salarie.id}
            )

            return redirect("paie:cabinet_liste_salaries_client", client_id=client.id)
    else:
        form = SalarieForm(instance=salarie)

    return render(request, "paie/salaries/modifier.html", {
        "client": client,
        "form": form,
        "salarie": salarie,
    })


@login_required
def sortie_salarie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)
    client = salarie.client

    if request.method == "POST":
        date_sortie = request.POST.get("date_sortie")

        if date_sortie:
            salarie.date_sortie = date_sortie
            salarie.actif = False
            salarie.save()

            # ⭐ AUDIT
            audit(
                client=client,
                user=request.user,
                action=f"Cabinet : sortie du salarié {salarie.nom}",
                metadata={"salarie_id": salarie.id, "date_sortie": date_sortie}
            )

        return redirect("paie:cabinet_liste_salaries_client", client_id=client.id)

    return redirect("paie:cabinet_modifier_salarie", salarie_id=salarie.id)


@login_required
def supprimer_salarie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)
    client = salarie.client

    # ⭐ AUDIT
    audit(
        client=client,
        user=request.user,
        action=f"Cabinet : suppression du salarié {salarie.nom}",
        metadata={"salarie_id": salarie.id}
    )

    salarie.delete()
    return redirect("paie:cabinet_liste_salaries_client", client_id=client.id)


@login_required
def cabinet_fiche_salarie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)

    # ⭐ AUDIT
    audit(
        client=salarie.client,
        user=request.user,
        action=f"Cabinet : consultation de la fiche salarié {salarie.nom}",
        metadata={"salarie_id": salarie.id}
    )

    return render(request, "paie/cabinet/salaries/fiche_salarie.html", {
        "salarie": salarie
    })


@login_required
def cabinet_salarie_remunerations(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)

    variables = VariablePaie.objects.filter(
        salarie=salarie
    ).select_related("paie_mois").order_by("-paie_mois__annee", "-paie_mois__mois")

    # ⭐ AUDIT
    audit(
        client=salarie.client,
        user=request.user,
        action=f"Cabinet : consultation des rémunérations du salarié {salarie.nom}",
        metadata={"salarie_id": salarie.id}
    )

    return render(request, "paie/cabinet/salaries/remunerations.html", {
        "salarie": salarie,
        "variables": variables,
    })



# ----------------------------------------------------
#   VARIABLES DE PAIE
# ----------------------------------------------------

from datetime import date
import calendar
from django.db import models

from datetime import date
from django.db import models
import calendar

@login_required
def variables_paie_salaries(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    # ⭐ AUDIT
    audit(
        client=paie_mois.client,
        user=request.user,
        action=f"Cabinet : consultation des variables du mois {paie_mois.mois}/{paie_mois.annee}",
        metadata={"mois_id": paie_mois.id}
    )

    date_debut_mois = date(paie_mois.annee, paie_mois.mois, 1)
    dernier_jour = calendar.monthrange(paie_mois.annee, paie_mois.mois)[1]
    date_fin_mois = date(paie_mois.annee, paie_mois.mois, dernier_jour)

    salaries = Salarie.objects.filter(
        client=paie_mois.client
    ).filter(
        models.Q(actif=True) |
        models.Q(date_sortie__isnull=True) |
        models.Q(date_sortie__gte=date_debut_mois)
    ).order_by("nom")

    variables_dict = {
        v.salarie_id: v
        for v in VariablePaie.objects.filter(paie_mois=paie_mois)
    }

    return render(request, "paie/variables/liste_salaries.html", {
        "paie_mois": paie_mois,
        "salaries": salaries,
        "variables_dict": variables_dict,
    })





@login_required
def saisie_variables_salarie(request, paie_mois_id, salarie_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)
    salarie = get_object_or_404(Salarie, id=salarie_id)

    variables, created = VariablePaie.objects.get_or_create(
        paie_mois=paie_mois,
        salarie=salarie
    )

    if request.method == "POST":
        variables.heures_sup_25 = request.POST.get("heures_sup_25", "")
        variables.heures_sup_50 = request.POST.get("heures_sup_50", "")
        variables.primes = request.POST.get("primes", "")
        variables.conges_debut = request.POST.get("conges_debut", "")
        variables.conges_fin = request.POST.get("conges_fin", "")
        variables.absences_maladie = request.POST.get("absences_maladie", "")
        variables.absences_autres = request.POST.get("absences_autres", "")
        variables.acomptes = request.POST.get("acomptes", "")
        variables.autres_infos = request.POST.get("autres_infos", "")
        variables.save()

        # ⭐ AUDIT : modification
        audit(
            client=paie_mois.client,
            user=request.user,
            action=f"Cabinet : modification des variables du salarié {salarie.nom} pour {paie_mois.mois}/{paie_mois.annee}",
            metadata={"mois_id": paie_mois.id, "salarie_id": salarie.id}
        )

        return redirect("paie:variables_paie_salaries", paie_mois_id=paie_mois.id)

    # ⭐ AUDIT : consultation
    audit(
        client=paie_mois.client,
        user=request.user,
        action=f"Cabinet : consultation des variables du salarié {salarie.nom} pour {paie_mois.mois}/{paie_mois.annee}",
        metadata={"mois_id": paie_mois.id, "salarie_id": salarie.id}
    )

    return render(request, "paie/variables/saisie.html", {
        "paie_mois": paie_mois,
        "salarie": salarie,
        "variables": variables,
    })



# ----------------------------------------------------
#   CLIENTS AVEC PAIE
# ----------------------------------------------------

from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from paie.models import Client, PaieMois

@login_required
def clients_paie(request):
    clients = (
        Client.objects
        .filter(module_paie=True)
        .annotate(
            nb_salaries_actifs=Count(
                "salaries",
                filter=Q(salaries__actif=True)
            )
        )
        .order_by("nom")
    )

    for c in clients:
        dernier = (
            PaieMois.objects
            .filter(client=c, bs_fait=True, dsn_faite=True)
            .order_by("-annee", "-mois")
            .first()
        )
        c.dernier_mois_traite = dernier

    # ⭐ AUDIT
    audit(
        client=None,
        user=request.user,
        action="Cabinet : consultation de la liste des clients paie",
        metadata={}
    )

    return render(request, "paie/cabinet/clients_paie.html", {
        "clients": clients,
    })


# ----------------------------------------------------
#   GESTION PAIE ANNUEL
# ----------------------------------------------------


from types import SimpleNamespace
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from paie.models import Client, PaieMois

@login_required
def cabinet_suivi_annuel(request):
    annee = request.GET.get("annee")
    if annee is None:
        annee = timezone.now().year
    else:
        annee = int(annee)

    annees = range(2023, timezone.now().year + 1)

    clients = (
        Client.objects
        .filter(module_paie=True)
        .order_by("nom")
    )

    mois_range = range(1, 13)

    for c in clients:
        suivi = []
        for m in mois_range:
            suivi.append(SimpleNamespace(
                mois=m,
                client=False,
                bs=False,
                dsn=False
            ))

        mois = PaieMois.objects.filter(client=c, annee=annee)

        for m in mois:
            item = suivi[m.mois - 1]
            item.client = m.client_valide
            item.bs = m.bs_fait
            item.dsn = m.dsn_faite
            item.bs_a_verifier = m.bs_a_verifier
            item.bs_verifie_par_cabinet = m.bs_verifie_par_cabinet

        c.suivi = suivi

    # ⭐ AUDIT
    audit(
        client=None,
        user=request.user,
        action=f"Cabinet : consultation du suivi annuel paie ({annee})",
        metadata={"annee": annee}
    )

    return render(request, "paie/cabinet/suivi_annuel.html", {
        "clients": clients,
        "annee": annee,
        "annees": annees,
        "mois_range": mois_range,
    })

# ----------------------------------------------------
#   CREATION DU MOIS DE PAIE
# ----------------------------------------------------

@login_required
def creer_mois_paie(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    today = timezone.now()
    annee = today.year
    mois = today.month

    paie_mois, created = PaieMois.objects.get_or_create(
        client=client,
        annee=annee,
        mois=mois
    )

    # ⭐ AUDIT
    audit(
        client=client,
        user=request.user,
        action=f"Cabinet : création du mois {mois}/{annee}",
        metadata={"mois_id": paie_mois.id}
    )

    return redirect("paie:variables_paie_salaries", paie_mois_id=paie_mois.id)


@login_required
def creer_mois_suivant(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    dernier = PaieMois.objects.filter(client=client).order_by("-annee", "-mois").first()

    if not dernier:
        nouveau_mois = 1
        nouvelle_annee = timezone.now().year
    else:
        if dernier.mois == 12:
            nouveau_mois = 1
            nouvelle_annee = dernier.annee + 1
        else:
            nouveau_mois = dernier.mois + 1
            nouvelle_annee = dernier.annee

    nouveau = PaieMois.objects.create(
        client=client,
        mois=nouveau_mois,
        annee=nouvelle_annee
    )

    # ⭐ AUDIT
    audit(
        client=client,
        user=request.user,
        action=f"Cabinet : création du mois {nouveau_mois}/{nouvelle_annee}",
        metadata={"mois_id": nouveau.id}
    )

    return redirect("paie:liste_mois_client", client_id=client.id)



from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from paie.models import PaieMois
from dossiers.models import NotificationPaie


@login_required
def valider_mois_client(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    if request.method == "POST":

        paie_mois.client_valide = True
        paie_mois.date_validation_client = timezone.now()
        paie_mois.save()

        # ⭐ AUDIT : validation du mois
        audit(
            client=paie_mois.client,
            user=request.user,
            action=f"Cabinet : validation du mois {paie_mois.mois}/{paie_mois.annee} pour le client",
            metadata={"mois_id": paie_mois.id}
        )

        # Calcul du mois suivant
        annee = paie_mois.annee
        mois = paie_mois.mois + 1
        if mois == 13:
            mois = 1
            annee += 1

        suivant, created = PaieMois.objects.get_or_create(
            client=paie_mois.client,
            annee=annee,
            mois=mois
        )

        # ⭐ AUDIT : création automatique du mois suivant
        audit(
            client=paie_mois.client,
            user=request.user,
            action=f"Cabinet : création automatique du mois {mois}/{annee}",
            metadata={"mois_id": suivant.id}
        )

        NotificationPaie.objects.create(
            client=paie_mois.client,
            paie_mois=paie_mois,
            lu_cabinet=False,
            lu_partenaire=False
        )

        # ⭐ AUDIT : notification envoyée
        audit(
            client=paie_mois.client,
            user=request.user,
            action=f"Cabinet : notification envoyée pour le mois {paie_mois.mois}/{paie_mois.annee}",
            metadata={"mois_id": paie_mois.id}
        )

        messages.success(
            request,
            "Mois validé. Le mois suivant a été créé automatiquement et une notification a été envoyée au cabinet."
        )

        return redirect("paie:variables_paie_salaries", paie_mois_id=paie_mois.id)

    return redirect("paie:variables_paie_salaries", paie_mois_id=paie_mois.id)


@login_required
def devalider_mois(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    paie_mois.client_valide = False
    paie_mois.date_validation_client = None
    paie_mois.bs_fait = False
    paie_mois.date_bs_fait = None
    paie_mois.dsn_faite = False
    paie_mois.date_dsn_faite = None
    paie_mois.save()

    # ⭐ AUDIT
    audit(
        client=paie_mois.client,
        user=request.user,
        action=f"Cabinet : dévalidation du mois {paie_mois.mois}/{paie_mois.annee}",
        metadata={"mois_id": paie_mois.id}
    )

    messages.success(request, "Le mois a été dévalidé. Le client peut à nouveau modifier les variables.")
    return redirect("paie:liste_mois_client", client_id=paie_mois.client.id)


# ----------------------------------------------------
#  LISTE DES MOIS DE PAIE
# ----------------------------------------------------

@login_required
def liste_mois_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    mois_list = PaieMois.objects.filter(client=client).order_by('-annee', '-mois')

    # ⭐ AUDIT
    audit(
        client=client,
        user=request.user,
        action=f"Cabinet : consultation de la liste des mois du client {client.nom}",
        metadata={"client_id": client.id}
    )

    return render(request, "paie/mois/liste_mois.html", {
        "client": client,
        "mois_list": mois_list,
    })


from django.template.loader import get_template
from django.http import HttpResponse

from dossiers.notifications import envoyer_relance_client

@login_required
def relancer_mois_client(request, paie_mois_id):
    mois = get_object_or_404(PaieMois, id=paie_mois_id)

    if mois.client_valide:
        messages.warning(request, "Ce mois est déjà validé par le client.")
        return redirect("paie:liste_mois_client", client_id=mois.client.id)

    envoyer_relance_client(mois)

    # ⭐ AUDIT
    audit(
        client=mois.client,
        user=request.user,
        action=f"Cabinet : relance envoyée pour le mois {mois.mois}/{mois.annee}",
        metadata={"mois_id": mois.id}
    )

    messages.success(request, "Relance envoyée au client.")
    return redirect("paie:liste_mois_client", client_id=mois.client.id)



# ----------------------------------------------------
#  FORCER LA VALIDATION DU MOIS
# ----------------------------------------------------

@login_required
def forcer_validation_mois(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    bs_forced = False
    dsn_forced = False

    if not paie_mois.bs_fait:
        paie_mois.bs_fait = True
        paie_mois.date_bs_fait = timezone.now()
        paie_mois.bs_force = True
        bs_forced = True

    if not paie_mois.dsn_faite:
        paie_mois.dsn_faite = True
        paie_mois.date_dsn_faite = timezone.now()
        paie_mois.dsn_force = True
        dsn_forced = True

    paie_mois.save()

    # ⭐ AUDIT
    audit(
        client=paie_mois.client,
        user=request.user,
        action=f"Cabinet : validation forcée du mois {paie_mois.mois}/{paie_mois.annee}",
        metadata={
            "mois_id": paie_mois.id,
            "bs_forced": bs_forced,
            "dsn_forced": dsn_forced
        }
    )

    messages.success(request, "Validation forcée appliquée (uniquement ce qui manquait).")
    return redirect("paie:liste_mois_client", client_id=paie_mois.client.id)


# ----------------------------------------------------
#  VALIDER LE MOIS POUR LE CLIENT (AVEC DEPART DE MAILS)
# ----------------------------------------------------

from django.utils import timezone
from dossiers.notifications import envoyer_notifications_paie

@login_required
def valider_pour_client(request, paie_mois_id):
    mois = get_object_or_404(PaieMois, id=paie_mois_id)

    if mois.client_valide:
        messages.warning(request, "Ce mois est déjà validé par le client.")
        return redirect("paie:liste_mois_client", client_id=mois.client.id)

    mois.client_valide = True
    mois.client_valide_par_cabinet = True
    mois.date_validation_par_cabinet = timezone.now()
    mois.save()

    envoyer_notifications_paie(mois)

    # ⭐ AUDIT
    audit(
        client=mois.client,
        user=request.user,
        action=f"Cabinet : validation du mois {mois.mois}/{mois.annee} pour le client",
        metadata={"mois_id": mois.id}
    )

    messages.success(request, "Le mois a été validé pour le client et les notifications ont été envoyées.")
    return redirect("paie:liste_mois_client", client_id=mois.client.id)


@login_required
def paie_bs_verifie_par_cabinet(request, paie_id):
    paie = get_object_or_404(PaieMois, id=paie_id)

    paie.bs_verifie_par_cabinet = True
    paie.date_bs_verifie_par_cabinet = timezone.now()
    paie.save()

    envoyer_notifications_bs_verifie(paie)

    # ⭐ AUDIT
    audit(
        client=paie.client,
        user=request.user,
        action=f"Cabinet : BS vérifié pour le mois {paie.mois}/{paie.annee}",
        metadata={"mois_id": paie.id}
    )

    messages.success(request, "Le BS a été vérifié par le cabinet.")
    return redirect("paie:liste_mois_client", paie.client.id)

