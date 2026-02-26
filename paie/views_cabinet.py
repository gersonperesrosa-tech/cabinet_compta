from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages

from .models import Client, Salarie, PaieMois, VariablePaie
from .forms import VariablePaieForm


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
    salaries = client.salaries.all()

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
            return redirect("paie:cabinet_liste_salaries_client", client_id=client.id)
    else:
        form = SalarieForm(instance=salarie)

    return render(request, "paie/salaries/modifier.html", {
        "client": client,
        "form": form,
        "salarie": salarie,
    })


@login_required
def supprimer_salarie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)
    client_id = salarie.client.id
    salarie.delete()
    return redirect("paie:cabinet_liste_salaries_client", client_id=client_id)

# ----------------------------------------------------
#   VARIABLES DE PAIE
# ----------------------------------------------------

@login_required
def variables_paie_salaries(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)
    salaries = Salarie.objects.filter(client=paie_mois.client)

    # On récupère les variables existantes pour chaque salarié
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
        form = VariablePaieForm(request.POST, instance=variables)
        if form.is_valid():
            form.save()
            return redirect("paie:variables_paie_salaries", paie_mois_id=paie_mois.id)
    else:
        form = VariablePaieForm(instance=variables)

    return render(request, "paie/variables/saisie.html", {
        "paie_mois": paie_mois,
        "salarie": salarie,
        "form": form,
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
    # 1. Récupération des clients avec module paie
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

    # 2. Ajout du dernier mois totalement traité (BS + DSN)
    for c in clients:
        dernier = (
            PaieMois.objects
            .filter(
                client=c,
                bs_fait=True,
                dsn_faite=True
            )
            .order_by("-annee", "-mois")
            .first()
        )

        c.dernier_mois_traite = dernier

    # 3. Envoi au template
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
    # Année sélectionnée ou année courante
    annee = request.GET.get("annee")
    if annee is None:
        annee = timezone.now().year
    else:
        annee = int(annee)

    # Liste des années disponibles (tu peux ajuster le début)
    annees = range(2023, timezone.now().year + 1)

    # Clients avec module paie
    clients = (
        Client.objects
        .filter(module_paie=True)
        .order_by("nom")
    )

    mois_range = range(1, 13)

    for c in clients:
        # Liste ordonnée des 12 mois
        suivi = []

        # Initialisation
        for m in mois_range:
            suivi.append(SimpleNamespace(
                mois=m,
                client=False,
                bs=False,
                dsn=False
            ))

        # Récupération des mois existants
        mois = PaieMois.objects.filter(client=c, annee=annee)

        for m in mois:
            item = suivi[m.mois - 1]  # index 0 = janvier
            item.client = m.client_valide
            item.bs = m.bs_fait
            item.dsn = m.dsn_faite

        c.suivi = suivi

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

    PaieMois.objects.create(
        client=client,
        mois=nouveau_mois,
        annee=nouvelle_annee
    )

    return redirect("paie:liste_mois_client", client_id=client.id)


@login_required
def valider_mois_client(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    if request.method == "POST":
        # 1. Valider le mois
        paie_mois.client_valide = True
        paie_mois.date_validation_client = timezone.now()
        paie_mois.save()

        # 2. Calcul du mois suivant
        annee = paie_mois.annee
        mois = paie_mois.mois + 1
        if mois == 13:
            mois = 1
            annee += 1

        # 3. Création automatique du mois suivant
        PaieMois.objects.get_or_create(
            client=paie_mois.client,
            annee=annee,
            mois=mois
        )

        messages.success(request, "Mois validé. Le mois suivant a été créé automatiquement.")
        return redirect("paie:variables_paie_salaries", paie_mois_id=paie_mois.id)

    return redirect("paie:variables_paie_salaries", paie_mois_id=paie_mois.id)

@login_required
def devalider_mois(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)

    # Réinitialisation des validations
    paie_mois.client_valide = False
    paie_mois.date_validation_client = None

    paie_mois.bs_fait = False
    paie_mois.date_bs_fait = None

    paie_mois.dsn_faite = False
    paie_mois.date_dsn_faite = None

    paie_mois.save()

    messages.success(request, "Le mois a été dévalidé. Le client peut à nouveau modifier les variables.")
    return redirect("paie:liste_mois_client", client_id=paie_mois.client.id)


# ----------------------------------------------------
#  LISTE DES MOIS DE PAIE
# ----------------------------------------------------

@login_required
def liste_mois_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    mois_list = PaieMois.objects.filter(client=client).order_by('-annee', '-mois')

    return render(request, "paie/mois/liste_mois.html", {
        "client": client,
        "mois_list": mois_list,
    })

from django.template.loader import get_template
from django.http import HttpResponse

@login_required
def export_pdf_variables(request, paie_mois_id):
    paie_mois = get_object_or_404(PaieMois, id=paie_mois_id)
    variables = VariablePaie.objects.filter(paie_mois=paie_mois).select_related("salarie")

    template_path = "paie/pdf/variables_paie_pdf.html"
    context = {
        "paie_mois": paie_mois,
        "variables": variables,
    }

    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=variables_paie_{paie_mois.mois}_{paie_mois.annee}.pdf"

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Erreur lors de la génération du PDF", status=500)

    return response
