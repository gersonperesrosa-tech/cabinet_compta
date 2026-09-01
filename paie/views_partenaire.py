from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from paie.models import Client, PaieMois, Salarie, VariablePaie
from dossiers.models import NotificationPaie
from django.utils import timezone
from django.contrib import messages
from dossiers.notifications import (
    envoyer_notifications_bs,
    envoyer_notifications_dsn,
    envoyer_notifications_bs_a_verifier,
)
from dossiers.audit import audit




@login_required
def partenaire_liste_clients(request):
    clients = Client.objects.filter(module_paie=True).order_by("nom")

    for c in clients:
        c.dernier_mois_traite = (
            PaieMois.objects
            .filter(client=c, bs_fait=True, dsn_faite=True)
            .order_by("-annee", "-mois")
            .first()
        )

        c.mois_valide_client = (
            PaieMois.objects
            .filter(client=c, client_valide=True, bs_fait=False)
            .order_by("-annee", "-mois")
            .first()
        )

        c.nb_actifs = Salarie.objects.filter(client=c, actif=True).count()

    #  AUDIT
    audit(
        client=None,
        user=request.user,
        action="Partenaire : consultation de la liste des clients paie",
        metadata={}
    )

    return render(request, "paie/partenaire/liste_clients.html", {
        "clients": clients
    })



from datetime import datetime

from django.utils import timezone

@login_required
def partenaire_dashboard(request):
    clients = Client.objects.filter(module_paie=True)

    today = timezone.now()
    annee = today.year
    mois = today.month

    mois_courant_qs = PaieMois.objects.filter(
        client__in=clients,
        annee=annee,
        mois=mois,
    )

    kpi_ouverts = mois_courant_qs.values("client").distinct().count()
    kpi_faits = mois_courant_qs.filter(bs_fait=True, dsn_faite=True).values("client").distinct().count()
    kpi_a_faire = mois_courant_qs.exclude(bs_fait=True, dsn_faite=True).values("client").distinct().count()

    notifications = NotificationPaie.objects.filter(lu_partenaire=False).select_related("client", "paie_mois")

    # ⭐ AUDIT
    audit(
        client=None,
        user=request.user,
        action="Partenaire : consultation du dashboard paie",
        metadata={}
    )

    return render(request, "paie/partenaire/dashboard.html", {
        "kpi_ouverts": kpi_ouverts,
        "kpi_faits": kpi_faits,
        "kpi_a_faire": kpi_a_faire,
        "annee": annee,
        "mois": mois,
        "notifications": notifications,
    })



@login_required
def partenaire_mois_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    mois_list = PaieMois.objects.filter(client=client).order_by("-annee", "-mois")

    # ⭐ AUDIT
    audit(
        client=client,
        user=request.user,
        action=f"Partenaire : consultation des mois du client {client.nom}",
        metadata={"client_id": client.id}
    )

    return render(request, "paie/partenaire/mois_client.html", {
        "client": client,
        "mois_list": mois_list
    })



from datetime import date
from django.db import models
import calendar

from datetime import date
from django.db import models
import calendar

@login_required
def partenaire_variables_mois(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    date_debut_mois = date(paie_mois.annee, paie_mois.mois, 1)

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

    lignes = []
    for s in salaries:
        present_ce_mois = (
            s.actif or
            s.date_sortie is None or
            s.date_sortie >= date_debut_mois
        )

        lignes.append({
            "salarie": s,
            "variables": variables_dict.get(s.id),
            "present_ce_mois": present_ce_mois,
        })

    # ⭐ AUDIT
    audit(
        client=paie_mois.client,
        user=request.user,
        action=f"Partenaire : consultation des variables du mois {paie_mois.mois}/{paie_mois.annee}",
        metadata={"mois_id": paie_mois.id}
    )

    return render(request, "paie/partenaire/variables_mois.html", {
        "paie_mois": paie_mois,
        "lignes": lignes,
    })



@login_required
def partenaire_detail_salarie_mois(request, paie_mois_id, salarie_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)
    salarie = get_object_or_404(Salarie, id=salarie_id)

    variables = VariablePaie.objects.filter(
        paie_mois=paie_mois,
        salarie=salarie
    ).first()

    # ⭐ AUDIT
    audit(
        client=paie_mois.client,
        user=request.user,
        action=f"Partenaire : consultation du salarié {salarie.nom} pour {paie_mois.mois}/{paie_mois.annee}",
        metadata={"mois_id": paie_mois.id, "salarie_id": salarie.id}
    )

    return render(request, "paie/partenaire/detail_salarie_mois.html", {
        "paie_mois": paie_mois,
        "salarie": salarie,
        "variables": variables,
    })


@login_required
def paie_bs_a_verifier(request, paie_id):
    paie = get_object_or_404(PaieMois, id=paie_id)

    paie.bs_a_verifier = True
    paie.date_bs_a_verifier = timezone.now()
    paie.save()

    envoyer_notifications_bs_a_verifier(paie)

    # ⭐ AUDIT
    audit(
        client=paie.client,
        user=request.user,
        action=f"Partenaire : BS envoyé au cabinet pour vérification ({paie.mois}/{paie.annee})",
        metadata={"mois_id": paie.id}
    )

    messages.success(request, "Le BS a été envoyé au cabinet pour vérification.")
    return redirect("paie:partenaire_mois_client", paie.client.id)


@login_required
def partenaire_bs_fait(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    if request.method == "POST":
        paie_mois.bs_fait = True
        paie_mois.date_bs_fait = timezone.now()
        paie_mois.bs_force = False
        paie_mois.save()

        envoyer_notifications_bs(paie_mois)

        # ⭐ AUDIT
        audit(
            client=paie_mois.client,
            user=request.user,
            action=f"Partenaire : BS validé pour {paie_mois.mois}/{paie_mois.annee}",
            metadata={"mois_id": paie_mois.id}
        )

    return redirect("paie:partenaire_variables_mois", paie_mois_id=paie_mois.id)



@login_required
def partenaire_dsn_faite(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    if request.method == "POST":
        paie_mois.dsn_faite = True
        paie_mois.date_dsn_faite = timezone.now()
        paie_mois.dsn_force = False
        paie_mois.save()

        envoyer_notifications_dsn(paie_mois)

        # ⭐ AUDIT
        audit(
            client=paie_mois.client,
            user=request.user,
            action=f"Partenaire : DSN validée pour {paie_mois.mois}/{paie_mois.annee}",
            metadata={"mois_id": paie_mois.id}
        )

    return redirect("paie:partenaire_variables_mois", paie_mois_id=paie_mois.id)



@login_required
def notification_lue(request, notif_id):
    notif = get_object_or_404(NotificationPaie, id=notif_id)
    notif.lu_partenaire = True
    notif.save()

    # ⭐ AUDIT
    audit(
        client=notif.client,
        user=request.user,
        action=f"Partenaire : notification lue (mois {notif.paie_mois.mois}/{notif.paie_mois.annee})",
        metadata={"notif_id": notif.id}
    )

    return redirect("paie:partenaire_dashboard")
