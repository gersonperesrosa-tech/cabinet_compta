from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from paie.models import Client, PaieMois, Salarie, VariablePaie
from django.utils import timezone


@login_required
def partenaire_liste_clients(request):
    # Tous les clients ayant le module paie actif
    clients = Client.objects.filter(module_paie=True)

    for c in clients:
        # Dernier mois traité (BS + DSN faites)
        c.dernier_mois_traite = (
            PaieMois.objects
            .filter(client=c, bs_fait=True, dsn_faite=True)
            .order_by("-annee", "-mois")
            .first()
        )

        # Nombre de salariés actifs
        c.nb_actifs = Salarie.objects.filter(client=c, actif=True).count()

    return render(request, "paie/partenaire/liste_clients.html", {
        "clients": clients
    })


from datetime import datetime

from django.utils import timezone

@login_required
def partenaire_dashboard(request):
    # Tous les clients paie
    clients = Client.objects.filter(module_paie=True)

    # Mois courant
    today = timezone.now()
    annee = today.year
    mois = today.month

    # Tous les PaieMois du mois courant pour ces clients
    mois_courant_qs = PaieMois.objects.filter(
        client__in=clients,
        annee=annee,
        mois=mois,
    )

    # KPI 1 : clients avec mois actuel ouvert (mois créé)
    kpi_ouverts = (
        mois_courant_qs
        .values("client")
        .distinct()
        .count()
    )

    # KPI 2 : clients avec mois actuel fait (BS + DSN faites)
    kpi_faits = (
        mois_courant_qs
        .filter(bs_fait=True, dsn_faite=True)
        .values("client")
        .distinct()
        .count()
    )

    # KPI 3 : clients avec mois actuel à faire (BS ou DSN manquantes)
    kpi_a_faire = (
        mois_courant_qs
        .exclude(bs_fait=True, dsn_faite=True)
        .values("client")
        .distinct()
        .count()
    )

    # Enrichir chaque client pour la liste détaillée
    for c in clients:
        mois_client = PaieMois.objects.filter(client=c)

        c.dernier_mois_traite = (
            mois_client
            .filter(bs_fait=True, dsn_faite=True)
            .order_by("-annee", "-mois")
            .first()
        )

        c.mois_en_attente = mois_client.filter(bs_fait=False).count()

    return render(request, "paie/partenaire/dashboard.html", {
        "clients": clients,
        "kpi_ouverts": kpi_ouverts,
        "kpi_faits": kpi_faits,
        "kpi_a_faire": kpi_a_faire,
        "annee": annee,
        "mois": mois,
    })


@login_required
def partenaire_mois_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    mois_list = PaieMois.objects.filter(client=client).order_by("-annee", "-mois")

    return render(request, "paie/partenaire/mois_client.html", {
        "client": client,
        "mois_list": mois_list
    })


@login_required
def partenaire_variables_mois(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)
    salaries = Salarie.objects.filter(client=paie_mois.client)

    variables_dict = {
        v.salarie_id: v
        for v in VariablePaie.objects.filter(paie_mois=paie_mois)
    }

    lignes = []
    for s in salaries:
        lignes.append({
            "salarie": s,
            "variables": variables_dict.get(s.id),
        })

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

    return render(request, "paie/partenaire/detail_salarie_mois.html", {
        "paie_mois": paie_mois,
        "salarie": salarie,
        "variables": variables,
    })


@login_required
def partenaire_bs_fait(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    if request.method == "POST":
        paie_mois.bs_fait = True
        paie_mois.date_bs_fait = timezone.now()
        paie_mois.save()

    return redirect("paie:partenaire_variables_mois", paie_mois_id=paie_mois.id)


@login_required
def partenaire_dsn_faite(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    if request.method == "POST":
        paie_mois.dsn_faite = True
        paie_mois.date_dsn_faite = timezone.now()
        paie_mois.save()

    return redirect("paie:partenaire_variables_mois", paie_mois_id=paie_mois.id)
