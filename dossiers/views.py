from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

from .models import Client, SuiviComptable, TVA, IS
from .forms import ClientForm, SuiviComptableForm, TVAForm, ISForm, ClotureClientForm
from .models import TVAAnnee, TVAModule, TVAClientAnnee, TVADeclaration, TVSDeclaration, DESDEBDeclaration, DividendesDeclaration, DPDeclaration, NoteTag, NoteCategorie, ClientNote, KanbanColumn, KanbanCard, KanbanTag, KanbanCardTag, ClotureAnnee, ClotureClient



# ----------------------------------------------------
#   CLIENTS
# ----------------------------------------------------
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from .models import Client
from .forms import ClientForm


from django.db.models.functions import Lower
from datetime import datetime

from django.db.models import Prefetch
from django.utils.timezone import now


from .models import (
    Client,
    TVAAnnee, TVAClientAnnee,
    AnneeFiscale, ClientModuleFiscal
)

@login_required
def liste_clients(request):
    # Tri alphabétique insensible à la casse
    clients = Client.objects.filter(archive=False).order_by(Lower("nom"))
    annee_en_cours = datetime.now().year

    # Récupération des objets année TVA et année fiscale
    tva_annee = TVAAnnee.objects.filter(annee=annee_en_cours).first()
    fiscale_annee = AnneeFiscale.objects.filter(annee=annee_en_cours).first()

    # Préchargement optimisé TVA + Fiscalité
    clients = clients.prefetch_related(
        Prefetch(
            "tvaclientannee_set",
            queryset=TVAClientAnnee.objects.filter(annee=tva_annee).select_related("module"),
            to_attr="tva_actuelle"
        ),
        Prefetch(
            "clientmodulefiscal_set",
            queryset=ClientModuleFiscal.objects.filter(annee=fiscale_annee).select_related("module"),
            to_attr="fiscal_actuel"
        )
    )

    form = ClientForm()  # ← tu gardes ton form

    return render(request, "dossiers/liste_clients.html", {
        "clients": clients,
        "annee_en_cours": annee_en_cours,
        "form": form,
    })

@login_required
def ajouter_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            return redirect('fiche_client', client.id)
    else:
        form = ClientForm()

    return render(request, 'dossiers/clients/ajouter_client.html', {
        'form': form
    })

@login_required
def archiver_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    client.archive = True
    client.save()
    return redirect('liste_clients')

@login_required
def restaurer_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    client.archive = False
    client.save()
    return redirect('archives_clients')

@login_required
def supprimer_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    client.delete()
    return redirect('liste_clients')

@login_required
def archives_clients(request):
    clients = Client.objects.filter(archive=True).order_by("nom")
    return render(request, 'dossiers/archives_clients.html', {'clients': clients})

# ----------------------------------------------------
#   SUIVI COMPTABLE (multi‑annuel)
# ----------------------------------------------------

@login_required
def suivi_comptable(request, client_id, annee):
    client = get_object_or_404(Client, id=client_id)

    annees_disponibles = list(range(2020, 2031))

    suivi = SuiviComptable.objects.filter(client=client, annee=annee).first()
    if not suivi:
        suivi = SuiviComptable.objects.create(client=client, annee=annee)

    if request.method == 'POST':
        form = SuiviComptableForm(request.POST, instance=suivi)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.saisi_par = request.user.username
            obj.save()
            return redirect('suivi_comptable', client_id=client.id, annee=annee)
    else:
        form = SuiviComptableForm(instance=suivi)

    return render(request, 'dossiers/suivi_comptable.html', {
        'form': form,
        'client': client,
        'suivi': suivi,
        'annee': annee,
        'annees_disponibles': annees_disponibles,
    })


# ----------------------------------------------------
#   SLIDEBAR : formulaire AJAX du suivi comptable
# ----------------------------------------------------

@login_required
def suivi_comptable_formulaire(request, client_id):
    suivi, created = SuiviComptable.objects.get_or_create(
        client_id=client_id,
        annee=2025
    )

    form = SuiviComptableForm(instance=suivi)

    return render(request, "dossiers/suivi_comptable_formulaire.html", {
        "form": form,
        "client_id": client_id
    })


# ----------------------------------------------------
#   SLIDEBAR : sauvegarde AJAX du suivi comptable
# ----------------------------------------------------

@require_POST
def suivi_comptable_save(request, client_id):
    suivi, created = SuiviComptable.objects.get_or_create(
        client_id=client_id,
        annee=2025
    )

    form = SuiviComptableForm(request.POST, instance=suivi)

    if form.is_valid():
        obj = form.save()

        return JsonResponse({
            "success": True,
            "client_id": client_id,
            "date_maj": obj.date_maj_compta.strftime("%d/%m/%Y") if obj.date_maj_compta else "–",
            "dernier_mois_traite": obj.dernier_mois_traite or "–",
            "saisi_par": obj.saisi_par or "–",
            "verifie": "✔️" if obj.verifie else "❌",
        })

    return JsonResponse({"success": False, "errors": form.errors}, status=400)



# ----------------------------------------------------
#   TVA (multi‑annuel)
# ----------------------------------------------------

@login_required
def tva_view(request, client_id, annee):
    client = get_object_or_404(Client, id=client_id)
    annees_disponibles = list(range(2020, 2031))

    tva = TVA.objects.filter(client=client, annee=annee).first()
    if not tva:
        tva = TVA.objects.create(client=client, annee=annee)

    if request.method == 'POST':
        form = TVAForm(request.POST, instance=tva)
        if form.is_valid():
            form.save()
            return redirect('tva', client_id=client.id, annee=annee)
    else:
        form = TVAForm(instance=tva)

    return render(request, 'dossiers/tva.html', {
        'form': form,
        'client': client,
        'tva': tva,
        'annee': annee,
        'annees_disponibles': annees_disponibles,
    })

# ----------------------------------------------------
#   TVA MENSUELLE (CA3M) : PAGE LISTE
# ----------------------------------------------------

@login_required
def tva_ca3m(request):
    # Année sélectionnée (par défaut : année en cours)
    annee = int(request.GET.get("annee", datetime.now().year))

    # Liste des années disponibles (tu peux ajuster)
    annees = list(range(2023, datetime.now().year + 2))

    clients = Client.objects.filter(
        archive=False,
        module_tva=True,
        regime_tva="CA3M"
    ).order_by("nom")

    tableau = []
    for client in clients:
        tva = TVA.objects.filter(client=client, annee=annee).first()
        if not tva:
            tva = TVA.objects.create(client=client, annee=annee)

        tableau.append({
            "client": client,
            "tva": tva
        })

    return render(request, "dossiers/tva/ca3m.html", {
        "tableau": tableau,
        "annee": annee,
        "annees": annees,
    })

@login_required
def tva_ca3t(request):
    return render(request, "dossiers/tva_placeholder.html")

@login_required
def tva_ca12(request):
    return render(request, "dossiers/tva_placeholder.html")

@login_required
def tva_franchise(request):
    return render(request, "dossiers/tva_placeholder.html")

@login_required
def tva_exo(request):
    return render(request, "dossiers/tva_placeholder.html")

# -------------------------
# HISTORIQUE TVA
# -------------------------


@login_required
def historique_tva(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    # On récupère l'historique (uniquement pour les années et la date de MAJ)
    historiques = HistoriqueTVA.objects.filter(client=client).order_by('-annee')

    tableau = []

    for h in historiques:

        # On récupère la TVA réelle de l'année (source de vérité)
        tva = TVA.objects.filter(client=client, annee=h.annee).first()

        # Si aucune TVA enregistrée → ligne vide
        if not tva:
            tableau.append({
                "annee": h.annee,
                "regime": h.regime_tva,
                "type": "AUCUN",
                "montants": {},
                "total": None,
                "updated": h.updated_at,
            })
            continue

        # ----------------------------------------------------
        # CA12 (Annuel)
        # ----------------------------------------------------
        if client.regime_tva == "CA12":
            montants = {
                "n_1": tva.ca12_montant_n_1,
                "s1_07": tva.ca12_s1_07,
                "s2_12": tva.ca12_s2_12,
            }

            total = sum([(m or 0) for m in montants.values()])

            tableau.append({
                "annee": h.annee,
                "regime": "CA12",
                "type": "CA12",
                "montants": montants,
                "total": total,
                "updated": h.updated_at,
            })
            continue

        # ----------------------------------------------------
        # CA3T (Trimestriel)
        # ----------------------------------------------------
        if client.regime_tva == "CA3T":
            montants = {
                "T1": tva.ca3t_t1,
                "T2": tva.ca3t_t2,
                "T3": tva.ca3t_t3,
                "T4": tva.ca3t_t4,
            }

            total = sum([(m or 0) for m in montants.values()])

            tableau.append({
                "annee": h.annee,
                "regime": "CA3T",
                "type": "CA3T",
                "montants": montants,
                "total": total,
                "updated": h.updated_at,
            })
            continue

        # ----------------------------------------------------
        # CA3M (Mensuel)
        # ----------------------------------------------------
        if client.regime_tva == "CA3M":
            montants = {
                "Jan": tva.tva_janvier,
                "Fév": tva.tva_fevrier,
                "Mar": tva.tva_mars,
                "Avr": tva.tva_avril,
                "Mai": tva.tva_mai,
                "Juin": tva.tva_juin,
                "Juil": tva.tva_juillet,
                "Août": tva.tva_aout,
                "Sep": tva.tva_septembre,
                "Oct": tva.tva_octobre,
                "Nov": tva.tva_novembre,
                "Déc": tva.tva_decembre,
            }

            total = sum([(m or 0) for m in montants.values()])

            tableau.append({
                "annee": h.annee,
                "regime": "CA3M",
                "type": "CA3M",
                "montants": montants,
                "total": total,
                "updated": h.updated_at,
            })
            continue

        # ----------------------------------------------------
        # FRANCHISE / EXONÉRÉ
        # ----------------------------------------------------
        tableau.append({
            "annee": h.annee,
            "regime": h.regime_tva,
            "type": "AUCUN",
            "montants": {},
            "total": None,
            "updated": h.updated_at,
        })

    return render(request, "dossiers/tva/historique_tva.html", {
        "client": client,
        "tableau": tableau,
    })

from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def tva_ca3m_formulaire(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    # 1) On récupère l'année envoyée dans l'URL (?annee=2025)
    annee = request.GET.get("annee")
    if annee is None:
        annee = datetime.now().year
    else:
        annee = int(annee)

    # 2) On récupère ou crée la TVA pour cette année
    tva = TVA.objects.filter(client=client, annee=annee).first()
    if not tva:
        tva = TVA.objects.create(client=client, annee=annee)

    # 3) On envoie aussi l'année au template
    return render(request, "dossiers/tva/ca3m_formulaire.html", {
        "client": client,
        "tva": tva,
        "annee": annee,
    })

from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from datetime import datetime

@login_required
def tva_ca3m_save(request, client_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Méthode non autorisée"})

    client = get_object_or_404(Client, id=client_id)

    # 1) Récupérer l'année envoyée dans l'URL
    annee = request.GET.get("annee")
    if annee is None:
        annee = datetime.now().year
    else:
        annee = int(annee)

    # 2) Récupérer ou créer la TVA pour cette année
    tva = TVA.objects.filter(client=client, annee=annee).first()
    if not tva:
        tva = TVA.objects.create(client=client, annee=annee)

    # 🔥 Fonction manquante → on la remet ici
    def to_decimal(value):
        if value in ["", None]:
            return Decimal("0")
        try:
            value = value.replace(",", ".")
            return Decimal(value)
        except (InvalidOperation, AttributeError):
            return Decimal("0")

    # -----------------------------
    # MONTANTS MENSUELS
    # -----------------------------
    tva.tva_janvier = to_decimal(request.POST.get("tva_janvier"))
    tva.tva_fevrier = to_decimal(request.POST.get("tva_fevrier"))
    tva.tva_mars = to_decimal(request.POST.get("tva_mars"))
    tva.tva_avril = to_decimal(request.POST.get("tva_avril"))
    tva.tva_mai = to_decimal(request.POST.get("tva_mai"))
    tva.tva_juin = to_decimal(request.POST.get("tva_juin"))
    tva.tva_juillet = to_decimal(request.POST.get("tva_juillet"))
    tva.tva_aout = to_decimal(request.POST.get("tva_aout"))
    tva.tva_septembre = to_decimal(request.POST.get("tva_septembre"))
    tva.tva_octobre = to_decimal(request.POST.get("tva_octobre"))
    tva.tva_novembre = to_decimal(request.POST.get("tva_novembre"))
    tva.tva_decembre = to_decimal(request.POST.get("tva_decembre"))

    # -----------------------------
    # STATUTS MENSUELS
    # -----------------------------
    tva.statut_janvier = request.POST.get("statut_janvier")
    tva.statut_fevrier = request.POST.get("statut_fevrier")
    tva.statut_mars = request.POST.get("statut_mars")
    tva.statut_avril = request.POST.get("statut_avril")
    tva.statut_mai = request.POST.get("statut_mai")
    tva.statut_juin = request.POST.get("statut_juin")
    tva.statut_juillet = request.POST.get("statut_juillet")
    tva.statut_aout = request.POST.get("statut_aout")
    tva.statut_septembre = request.POST.get("statut_septembre")
    tva.statut_octobre = request.POST.get("statut_octobre")
    tva.statut_novembre = request.POST.get("statut_novembre")
    tva.statut_decembre = request.POST.get("statut_decembre")

    # Sauvegarde finale
    tva.save()

    return JsonResponse({"status": "success"})

# ----------------------------------------------------
#   TVA MENSUELLE (CA3M) : SAUVEGARDE AJAX
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse

@login_required
def tva_mensuelle_save(request, client_id):
    if request.method == "POST":
        client = get_object_or_404(Client, id=client_id)

        # On récupère ou crée la TVA 2025
        tva = TVA.objects.filter(client=client, annee=2025).first()
        if not tva:
            tva = TVA.objects.create(client=client, annee=2025)

        # Fonction utilitaire pour convertir proprement en Decimal
        def to_decimal(value):
            if value in ["", None]:
                return Decimal("0")
            try:
                value = value.replace(",", ".")
                return Decimal(value)
            except (InvalidOperation, AttributeError):
                return Decimal("0")

        # -----------------------------
        # MONTANTS MENSUELS
        # -----------------------------
        tva.tva_janvier = to_decimal(request.POST.get("tva_janvier"))
        tva.tva_fevrier = to_decimal(request.POST.get("tva_fevrier"))
        tva.tva_mars = to_decimal(request.POST.get("tva_mars"))
        tva.tva_avril = to_decimal(request.POST.get("tva_avril"))
        tva.tva_mai = to_decimal(request.POST.get("tva_mai"))
        tva.tva_juin = to_decimal(request.POST.get("tva_juin"))
        tva.tva_juillet = to_decimal(request.POST.get("tva_juillet"))
        tva.tva_aout = to_decimal(request.POST.get("tva_aout"))
        tva.tva_septembre = to_decimal(request.POST.get("tva_septembre"))
        tva.tva_octobre = to_decimal(request.POST.get("tva_octobre"))
        tva.tva_novembre = to_decimal(request.POST.get("tva_novembre"))
        tva.tva_decembre = to_decimal(request.POST.get("tva_decembre"))

        # -----------------------------
        # STATUTS MENSUELS
        # -----------------------------
        tva.statut_janvier = request.POST.get("statut_janvier")
        tva.statut_fevrier = request.POST.get("statut_fevrier")
        tva.statut_mars = request.POST.get("statut_mars")
        tva.statut_avril = request.POST.get("statut_avril")
        tva.statut_mai = request.POST.get("statut_mai")
        tva.statut_juin = request.POST.get("statut_juin")
        tva.statut_juillet = request.POST.get("statut_juillet")
        tva.statut_aout = request.POST.get("statut_aout")
        tva.statut_septembre = request.POST.get("statut_septembre")
        tva.statut_octobre = request.POST.get("statut_octobre")
        tva.statut_novembre = request.POST.get("statut_novembre")
        tva.statut_decembre = request.POST.get("statut_decembre")

        # Sauvegarde finale
        tva.save()


    # 🔥 Historique TVA – ne doit JAMAIS casser la sauvegarde
    try:
        HistoriqueTVA.objects.update_or_create(
            client=client,
            annee=annee,
            defaults={
                "regime_tva": client.regime_tva,

                "ca3m_m1": tva.tva_janvier,
                "ca3m_m2": tva.tva_fevrier,
                "ca3m_m3": tva.tva_mars,
                "ca3m_m4": tva.tva_avril,
                "ca3m_m5": tva.tva_mai,
                "ca3m_m6": tva.tva_juin,
                "ca3m_m7": tva.tva_juillet,
                "ca3m_m8": tva.tva_aout,
                "ca3m_m9": tva.tva_septembre,
                "ca3m_m10": tva.tva_octobre,
                "ca3m_m11": tva.tva_novembre,
                "ca3m_m12": tva.tva_decembre,

                "ca3m_statut_m1": tva.statut_janvier,
                "ca3m_statut_m2": tva.statut_fevrier,
                "ca3m_statut_m3": tva.statut_mars,
                "ca3m_statut_m4": tva.statut_avril,
                "ca3m_statut_m5": tva.statut_mai,
                "ca3m_statut_m6": tva.statut_juin,
                "ca3m_statut_m7": tva.statut_juillet,
                "ca3m_statut_m8": tva.statut_aout,
                "ca3m_statut_m9": tva.statut_septembre,
                "ca3m_statut_m10": tva.statut_octobre,
                "ca3m_statut_m11": tva.statut_novembre,
                "ca3m_statut_m12": tva.statut_decembre,
            }
        )
    except Exception:
        # On ignore toute erreur d'historique pour ne pas bloquer la saisie
        pass


        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"})

# ----------------------------------------------------
#   CA3 TRIMESTRIELLE
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.shortcuts import render
from .models import Client, TVA

@login_required
def tva_ca3t(request):
    annee = int(request.GET.get("annee", datetime.now().year))
    annees = list(range(2023, datetime.now().year + 2))

    clients = Client.objects.filter(
        archive=False,
        module_tva=True,
        regime_tva="CA3T"
    ).order_by("nom")

    tableau = []

    for client in clients:
        tva, created = TVA.objects.get_or_create(client=client, annee=annee)

        tableau.append({
            "client": client,
            "tva": tva,

            # Pastilles trimestrielles
            "t1": tva.statut_1t,
            "t2": tva.statut_2t,
            "t3": tva.statut_3t,
            "t4": tva.statut_4t,

            # Montants trimestriels
            "m1": tva.tva_1t,
            "m2": tva.tva_2t,
            "m3": tva.tva_3t,
            "m4": tva.tva_4t,
        })

    return render(request, "dossiers/tva/ca3t.html", {
        "tableau": tableau,
        "annee": annee,
        "annees": annees,
    })

    # -----------------------------
    #   🔥 HISTORIQUE TVA
    # -----------------------------
    HistoriqueTVA.objects.update_or_create(
        client=client,
        annee=annee,
        defaults={
            "regime_tva": client.regime_tva,

            # Champs CA3T dédiés
            "ca3t_t1": tva.tva_1t,
            "ca3t_t2": tva.tva_2t,
            "ca3t_t3": tva.tva_3t,
            "ca3t_t4": tva.tva_4t,

            "ca3t_statut_t1": tva.statut_1t,
            "ca3t_statut_t2": tva.statut_2t,
            "ca3t_statut_t3": tva.statut_3t,
            "ca3t_statut_t4": tva.statut_4t,
        }
    )

    # -----------------------------
    #   REDIRECTION HTMX
    # -----------------------------
    return HttpResponse("<script>window.location.reload();</script>")



# ----------------------------------------------------
#   FICHE CLIENT (version mise à jour avec module_paie)
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Client
from .forms import ClientForm


@login_required
def fiche_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)

        if form.is_valid():
            client = form.save(commit=False)

            # --- Mise à jour du module Paie ---
            client.module_paie = "module_paie" in request.POST

            client.save()
            return redirect("liste_clients")

    else:
        form = ClientForm(instance=client)

    return render(request, "clients/fiche_client.html", {
        "form": form,
        "client": client,
    })
# ----------------------------------------------------
#   IS (multi‑annuel)
# ----------------------------------------------------

@login_required
def is_view(request, client_id, annee):
    client = get_object_or_404(Client, id=client_id)
    annees_disponibles = list(range(2020, 2031))

    is_fiscal = IS.objects.filter(client=client, annee=annee).first()
    if not is_fiscal:
        is_fiscal = IS.objects.create(client=client, annee=annee)

    if request.method == 'POST':
        form = ISForm(request.POST, instance=is_fiscal)
        if form.is_valid():
            form.save()
            return redirect('is', client_id=client.id, annee=annee)
    else:
        form = ISForm(instance=is_fiscal)

    couleurs = {
        "BLANC": "#B91C1C",
        "JAUNE": "#FFD700",
        "VERT_CLAIR": "#90EE90",
        "VERT_FONCE": "#006400",
    }

    acomptes = [
        {
            "nom": "1er acompte",
            "date": f"15/03/{annee}",
            "montant": is_fiscal.acompte_1,
            "statut": is_fiscal.statut_acompte_1,
            "couleur": couleurs.get(is_fiscal.statut_acompte_1, "#FFFFFF"),
        },
        {
            "nom": "2e acompte",
            "date": f"15/06/{annee}",
            "montant": is_fiscal.acompte_2,
            "statut": is_fiscal.statut_acompte_2,
            "couleur": couleurs.get(is_fiscal.statut_acompte_2, "#FFFFFF"),
        },
        {
            "nom": "3e acompte",
            "date": f"15/09/{annee}",
            "montant": is_fiscal.acompte_3,
            "statut": is_fiscal.statut_acompte_3,
            "couleur": couleurs.get(is_fiscal.statut_acompte_3, "#FFFFFF"),
        },
        {
            "nom": "4e acompte",
            "date": f"15/12/{annee}",
            "montant": is_fiscal.acompte_4,
            "statut": is_fiscal.statut_acompte_4,
            "couleur": couleurs.get(is_fiscal.statut_acompte_4, "#FFFFFF"),
        },
    ]

    return render(request, 'dossiers/is.html', {
        'form': form,
        'client': client,
        'is_fiscal': is_fiscal,
        'annee': annee,
        'annees_disponibles': annees_disponibles,
        'acomptes': acomptes,
    })


# ----------------------------------------------------
#   Créer l'année suivante
# ----------------------------------------------------

@login_required
def is_creer_annee_suivante(request, client_id, annee):
    client = get_object_or_404(Client, id=client_id)
    nouvelle_annee = annee + 1

    is_existant = IS.objects.filter(client=client, annee=nouvelle_annee).first()

    if not is_existant:
        IS.objects.create(client=client, annee=nouvelle_annee)

    return redirect('is', client_id=client.id, annee=nouvelle_annee)


# ----------------------------------------------------
#   AJAX : Mise à jour des pastilles TVA
# ----------------------------------------------------

@csrf_exempt
@require_POST
@staff_member_required
def tva_set_statut(request):
    tva_id = request.POST.get("tva_id")
    mois = request.POST.get("mois")
    statut = request.POST.get("statut")

    if not (tva_id and mois and statut):
        return JsonResponse({"success": False, "error": "Paramètres manquants"}, status=400)

    try:
        tva = TVA.objects.get(pk=tva_id)
    except TVA.DoesNotExist:
        return JsonResponse({"success": False, "error": "TVA introuvable"}, status=404)

    field_name = f"statut_{mois}"
    if not hasattr(tva, field_name):
        return JsonResponse({"success": False, "error": "Mois invalide"}, status=400)

    setattr(tva, field_name, statut)
    tva.save()

    return JsonResponse({"success": True})


# ----------------------------------------------------
#   DASHBOARD
# ----------------------------------------------------

@login_required
def dashboard(request):
    clients = Client.objects.filter(archive=False).order_by('nom')

    return render(request, 'dashboard/dashboard.html', {
        'clients': clients,
    })

# ----------------------------------------------------
#   SUIVI COMPTABLE : PAGE LISTE
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from datetime import date
from django.db.models.functions import Lower

@login_required
def liste_suivi_comptable(request):
    # On filtre :
    # - clients non archivés
    # - clients ayant le module "saisie comptable" activé
    clients = Client.objects.filter(
        archive=False,
        module_saisie=True
    ).order_by(Lower("nom"))

    suivis = {}
    annees = {}
    current_year = date.today().year

    for client in clients:
        suivi = SuiviComptable.objects.filter(client=client).order_by("-annee").first()
        suivis[client.id] = suivi

        if suivi and suivi.annee:
            annees[client.id] = suivi.annee
        else:
            annees[client.id] = current_year

    return render(request, "dossiers/liste_suivi_comptable.html", {
        "clients": clients,
        "suivis": suivis,
        "annees": annees,
        "current_year": current_year,
    })

# ----------------------------------------------------
#   SUIVI COMPTABLE : PAGE POPUP
# ----------------------------------------------------

@login_required
def popup_suivi_comptable(request, client_id, annee):
    client = get_object_or_404(Client, id=client_id)
    suivi = SuiviComptable.objects.filter(client=client, annee=annee).first()

    if not suivi:
        suivi = SuiviComptable.objects.create(client=client, annee=annee)

    if request.method == "POST":
        form = SuiviComptableForm(request.POST, instance=suivi)

        # Fonction pour nettoyer les décimaux FR → EN
        def clean_decimal(value):
            if not value:
                return None
            return value.replace(" ", "").replace("\xa0", "").replace(",", ".")

        if form.is_valid():
            obj = form.save(commit=False)

            # 🔥 Mettre à jour l'année depuis le formulaire
            annee_form = request.POST.get("annee")
            if annee_form:
                obj.annee = int(annee_form)

            # 🔥 AJOUT DES 3 NOUVEAUX CHAMPS
            obj.ca_actuel = clean_decimal(request.POST.get("ca_actuel"))
            obj.saisie_en_cours = "saisie_en_cours" in request.POST
            obj.saisie_terminee = "saisie_terminee" in request.POST

            obj.save()
            return JsonResponse({"success": True})

    else:
        form = SuiviComptableForm(instance=suivi)

    return render(request, "dossiers/popup_suivi_comptable.html", {
        "client": client,
        "suivi": suivi,
        "form": form,
    })

# ----------------------------------------------------
#   TVA CA3M CREATION D ANNEE SUIVANTE
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def tva_ca3m_creer_annee_suivante(request, annee):
    nouvelle_annee = annee + 1

    # On récupère tous les clients CA3M
    clients = Client.objects.filter(
        archive=False,
        module_tva=True,
        regime_tva="CA3M"
    )

    # On crée la TVA pour la nouvelle année si elle n'existe pas
    for client in clients:
        existe = TVA.objects.filter(client=client, annee=nouvelle_annee).exists()
        if not existe:
            TVA.objects.create(client=client, annee=nouvelle_annee)

    # On redirige vers la page CA3M avec la nouvelle année sélectionnée
    return redirect(f"/tva/ca3m/?annee={nouvelle_annee}")

# ----------------------------------------------------
#   TVA CA3T CREATION D ANNEE SUIVANTE
# ----------------------------------------------------

@login_required
def tva_ca3t_creer_annee_suivante(request, annee):
    nouvelle_annee = annee + 1
    return redirect(f"/tva/ca3t/?annee={nouvelle_annee}")


# ----------------------------------------------------
#   TVA CA12
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from .models import TVA_CA12, Client

@login_required
def tva_ca12(request):
    # Année sélectionnée ou année courante
    annee = int(request.GET.get("annee", datetime.now().year))

    # Liste des années disponibles (comme CA3M/CA3T)
    annees = list(range(2020, datetime.now().year + 2))

    # Clients CA12 uniquement
    clients = Client.objects.filter(
        module_tva=True,
        regime_tva="CA12"
    ).order_by("nom")

    tableau = []
    for client in clients:
        tva, _ = TVA_CA12.objects.get_or_create(client=client, annee=annee)
        tableau.append(tva)

    return render(request, "dossiers/tva/ca12.html", {
        "annee": annee,
        "annees": annees,
        "tableau": tableau,
    })

from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.http import HttpResponse

@login_required
def clean_decimal(value):
    if not value:
        return None
    return Decimal(value.replace(",", "."))

from .models import TVA_CA12, Client, HistoriqueTVA

@login_required
def tva_ca12_save(request, client_id, annee):
    client = get_object_or_404(Client, id=client_id)
    tva, _ = TVA_CA12.objects.get_or_create(client=client, annee=annee)

    # Montants CA12
    tva.montant_n_1 = clean_decimal(request.POST.get("montant_n_1"))
    tva.s1_07 = clean_decimal(request.POST.get("s1_07"))
    tva.s2_12 = clean_decimal(request.POST.get("s2_12"))

    # Statuts CA12
    tva.statut_s1_07 = clean_status(request.POST.get("statut_s1_07"))
    tva.statut_s2_12 = clean_status(request.POST.get("statut_s2_12"))

    # Commentaire TVA > 1000 €
    tva.commentaire_tva_sup_1000 = request.POST.get("commentaire_tva_sup_1000")

    tva.save()

    # 🔥 Mise à jour automatique de l'historique TVA (CA12)
    HistoriqueTVA.objects.update_or_create(
        client=client,
        annee=annee,
        defaults={
            "regime_tva": client.regime_tva,

            # Champs CA12 dédiés
            "ca12_montant_n_1": tva.montant_n_1,
            "ca12_s1_07": tva.s1_07,
            "ca12_s2_12": tva.s2_12,

            "ca12_statut_s1_07": tva.statut_s1_07,
            "ca12_statut_s2_12": tva.statut_s2_12,
        }
    )

    # Redirection HTMX propre
    response = HttpResponse()
    response['HX-Redirect'] = f"/tva/ca12/?annee={annee}"
    return response

@login_required
def tva_ca12_popup(request, client_id, annee):
    client = get_object_or_404(Client, id=client_id)
    tva, _ = TVA_CA12.objects.get_or_create(client=client, annee=annee)

    return render(request, "dossiers/tva/ca12_popup.html", {
        "client": client,
        "annee": annee,
        "tva": tva,
    })

@login_required
def clean_status(value):
    if not value:
        return None
    return value.strip().upper()

@login_required
def tva_ca12_creer_annee_suivante(request, annee):
    nouvelle_annee = annee + 1
    return redirect(f"/tva/ca12/?annee={nouvelle_annee}")

# ----------------------------------------------------
#   FRANCHISE TVA
# ----------------------------------------------------

@login_required
def tva_franchise(request):
    # Année sélectionnée ou année courante
    annee = int(request.GET.get("annee", datetime.now().year))

    # Liste des années disponibles
    annees = list(range(2020, datetime.now().year + 2))

    # Clients en franchise de TVA
    clients = Client.objects.filter(
        module_tva=True,
        regime_tva="FRANCHISE"
    ).order_by("nom")

    return render(request, "dossiers/tva/franchise.html", {
        "annee": annee,
        "annees": annees,
        "clients": clients,
    })



# ----------------------------------------------------
#   EXONERE TVA
# ----------------------------------------------------

@login_required
def tva_exoneres(request):
    # Année sélectionnée ou année courante
    annee = int(request.GET.get("annee", datetime.now().year))

    # Liste des années disponibles
    annees = list(range(2020, datetime.now().year + 2))

    # Clients exonérés de TVA
    clients = Client.objects.filter(
        module_tva=True,
        regime_tva="EXO"
    ).order_by("nom")

    return render(request, "dossiers/tva/exoneres.html", {
        "annee": annee,
        "annees": annees,
        "clients": clients,
    })


# ----------------------------------------------------
#   NOUVELLE STRUCTURE MODULES TVA
# ----------------------------------------------------


@login_required
def tva_creer_annee(request):
    if request.method == "POST":
        annee = request.POST.get("annee")

        if TVAAnnee.objects.filter(annee=annee).exists():
            messages.error(request, f"L'année {annee} existe déjà.")
            return redirect("tva_annees")

        # Création de l'année
        tva_annee = TVAAnnee.objects.create(annee=annee)

        # Création automatique des modules
        for type_module in ["CA3M", "CA3T", "CA12", "FR", "EXO"]:
            TVAModule.objects.create(annee=tva_annee, type=type_module)

        messages.success(request, f"L'année TVA {annee} a été créée avec ses modules.")
        return redirect("tva_annees")

    return redirect("tva_annees")

@login_required
def tva_modules_annee(request, annee_id):
    annee = get_object_or_404(TVAAnnee, id=annee_id)
    modules = annee.modules.all().order_by("type")

    return render(request, "tva/tva_modules_annee.html", {
        "annee": annee,
        "modules": modules,
    })

@login_required
def tva_clients_module(request, module_id):
    module = get_object_or_404(TVAModule, id=module_id)

    # Liste correcte : les objets TVAClientAnnee liés au module
    clients_module = TVAClientAnnee.objects.filter(module=module).select_related("client")

    # Tous les clients disponibles pour ajout
    tous_les_clients = Client.objects.all().order_by("nom")

    return render(request, "tva/tva_clients_module.html", {
        "module": module,
        "clients_module": clients_module,
        "tous_les_clients": tous_les_clients,
    })

@login_required
def tva_clients_module_ajouter(request, module_id):
    module = get_object_or_404(TVAModule, id=module_id)

    if request.method == "POST":
        client_id = request.POST.get("client_id")
        client = get_object_or_404(Client, id=client_id)

        TVAClientAnnee.objects.get_or_create(
            module=module,
            client=client,
            annee=module.annee  # ← OBLIGATOIRE
        )

        messages.success(request, f"{client.nom} a été ajouté au module {module.get_type_display()}.")
        return redirect("tva_clients_module", module_id=module.id)

    return redirect("tva_clients_module", module_id=module.id)

@login_required
def tva_clients_module_supprimer(request, client_annee_id):
    obj = get_object_or_404(TVAClientAnnee, id=client_annee_id)
    module_id = obj.module.id
    obj.delete()

    messages.success(request, "Client retiré du module.")
    return redirect("tva_clients_module", module_id=module_id)

@login_required
def tva_annees(request):
    annees = TVAAnnee.objects.order_by("-annee")
    return render(request, "tva/tva_annees.html", {"annees": annees})

from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import TVAClientAnnee, TVADeclaration

@login_required
def tva_saisie_ca3m(request, tva_client_annee_id):
    tca = get_object_or_404(TVAClientAnnee, id=tva_client_annee_id)

    # On récupère ou crée la déclaration TVA
    declaration, created = TVADeclaration.objects.get_or_create(
        tva_client_annee=tca
    )

    if request.method == "POST":
        def to_decimal(value):
            if value in ["", None]:
                return None
            try:
                return Decimal(value.replace(",", "."))
            except:
                return None

        # MONTANTS
        declaration.tva_janvier = to_decimal(request.POST.get("tva_janvier"))
        declaration.tva_fevrier = to_decimal(request.POST.get("tva_fevrier"))
        declaration.tva_mars = to_decimal(request.POST.get("tva_mars"))
        declaration.tva_avril = to_decimal(request.POST.get("tva_avril"))
        declaration.tva_mai = to_decimal(request.POST.get("tva_mai"))
        declaration.tva_juin = to_decimal(request.POST.get("tva_juin"))
        declaration.tva_juillet = to_decimal(request.POST.get("tva_juillet"))
        declaration.tva_aout = to_decimal(request.POST.get("tva_aout"))
        declaration.tva_septembre = to_decimal(request.POST.get("tva_septembre"))
        declaration.tva_octobre = to_decimal(request.POST.get("tva_octobre"))
        declaration.tva_novembre = to_decimal(request.POST.get("tva_novembre"))
        declaration.tva_decembre = to_decimal(request.POST.get("tva_decembre"))

        # STATUTS
        declaration.statut_janvier = request.POST.get("statut_janvier")
        declaration.statut_fevrier = request.POST.get("statut_fevrier")
        declaration.statut_mars = request.POST.get("statut_mars")
        declaration.statut_avril = request.POST.get("statut_avril")
        declaration.statut_mai = request.POST.get("statut_mai")
        declaration.statut_juin = request.POST.get("statut_juin")
        declaration.statut_juillet = request.POST.get("statut_juillet")
        declaration.statut_aout = request.POST.get("statut_aout")
        declaration.statut_septembre = request.POST.get("statut_septembre")
        declaration.statut_octobre = request.POST.get("statut_octobre")
        declaration.statut_novembre = request.POST.get("statut_novembre")
        declaration.statut_decembre = request.POST.get("statut_decembre")

        declaration.save()

        messages.success(request, "Déclaration TVA mensuelle enregistrée.")
        return redirect(request.path)

    return render(request, "tva/tva_saisie_ca3m.html", {
        "tca": tca,
        "declaration": declaration,
    })

from django.contrib.auth.decorators import login_required
from decimal import Decimal

@login_required
def tva_saisie_ca3t(request, tva_client_annee_id):
    tca = get_object_or_404(TVAClientAnnee, id=tva_client_annee_id)
    declaration, created = TVADeclaration.objects.get_or_create(tva_client_annee=tca)

    if request.method == "POST":

        def clean_decimal(value):
            if not value:
                return None
            value = value.replace(",", ".")
            try:
                return Decimal(value)
            except:
                return None

        # Montants trimestriels
        declaration.ca3t_t1 = clean_decimal(request.POST.get("ca3t_t1"))
        declaration.ca3t_t2 = clean_decimal(request.POST.get("ca3t_t2"))
        declaration.ca3t_t3 = clean_decimal(request.POST.get("ca3t_t3"))
        declaration.ca3t_t4 = clean_decimal(request.POST.get("ca3t_t4"))

        # Statuts trimestriels
        declaration.statut_t1 = request.POST.get("statut_t1") or "NONE"
        declaration.statut_t2 = request.POST.get("statut_t2") or "NONE"
        declaration.statut_t3 = request.POST.get("statut_t3") or "NONE"
        declaration.statut_t4 = request.POST.get("statut_t4") or "NONE"

        declaration.save()
        messages.success(request, "Déclaration trimestrielle enregistrée.")
        return redirect(request.path)

    return render(request, "tva/tva_saisie_ca3t.html", {
        "tca": tca,
        "declaration": declaration,
    })

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from .models import Client, TVA

@login_required
def tva_ca3t_formulaire(request, client_id, annee):
    client = get_object_or_404(Client, id=client_id)
    tca = get_object_or_404(TVAClientAnnee, client=client, annee__id=annee)

    declaration, created = TVADeclaration.objects.get_or_create(
        tva_client_annee=tca
    )

    return render(request, "dossiers/tva/ca3t_popup.html", {
        "client": client,
        "tca": tca,
        "declaration": declaration,
        "annee": annee,
    })

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from decimal import Decimal
from .models import Client, TVA, HistoriqueTVA

@login_required
def tva_ca3t_save(request, client_id, annee):
    client = get_object_or_404(Client, id=client_id)
    tca = get_object_or_404(TVAClientAnnee, client=client, annee__id=annee)

    declaration, created = TVADeclaration.objects.get_or_create(
        tva_client_annee=tca
    )

    def clean_decimal(value):
        if not value:
            return None
        value = value.replace(",", ".")
        try:
            return Decimal(value)
        except:
            return None

    # Montants
    declaration.ca3t_t1 = clean_decimal(request.POST.get("montant_t1"))
    declaration.ca3t_t2 = clean_decimal(request.POST.get("montant_t2"))
    declaration.ca3t_t3 = clean_decimal(request.POST.get("montant_t3"))
    declaration.ca3t_t4 = clean_decimal(request.POST.get("montant_t4"))

    # Statuts
    declaration.statut_t1 = request.POST.get("statut_t1") or "NONE"
    declaration.statut_t2 = request.POST.get("statut_t2") or "NONE"
    declaration.statut_t3 = request.POST.get("statut_t3") or "NONE"
    declaration.statut_t4 = request.POST.get("statut_t4") or "NONE"

    declaration.save()

    return HttpResponse("OK")

@login_required
def tva_saisie_ca12(request, tva_client_annee_id):
    tca = get_object_or_404(TVAClientAnnee, id=tva_client_annee_id)
    declaration, created = TVADeclaration.objects.get_or_create(tva_client_annee=tca)

    # ----------------------------------------------------
    # 🔧 Nettoyage des décimaux (amélioré)
    # ----------------------------------------------------
    def clean_decimal(value):
        if not value or value.strip() == "":
            return 0  # 🔥 On renvoie 0 au lieu de None

        value = value.replace("\xa0", "").replace(" ", "").replace(",", ".")
        try:
            return float(value)  # ou Decimal(value) si tu préfères
        except:
            return 0  # 🔥 Sécurité : si l'utilisateur tape n'importe quoi

    # ----------------------------------------------------
    # 🔥 CALCUL AUTOMATIQUE DU N-1
    # ----------------------------------------------------
    annee_actuelle = tca.annee.annee
    annee_precedente = annee_actuelle - 1

    declaration_prec = TVADeclaration.objects.filter(
        tva_client_annee__client=tca.client,
        tva_client_annee__annee__annee=annee_precedente
    ).first()

    if declaration_prec:
        n_1_calcule = (
            (declaration_prec.tva_acompte_1 or 0) +
            (declaration_prec.tva_acompte_2 or 0) +
            (declaration_prec.tva_solde or 0)
        )
    else:
        n_1_calcule = 0

    # ----------------------------------------------------
    # 🔥 SI GET : pré-remplir N-1 si vide
    # ----------------------------------------------------
    if request.method == "GET":
        if not declaration.tva_n_1:
            declaration.tva_n_1 = n_1_calcule
            declaration.save()

    # ----------------------------------------------------
    # 🔥 TRAITEMENT POST
    # ----------------------------------------------------
    if request.method == "POST":

        declaration.tva_n_1 = clean_decimal(request.POST.get("tva_n_1"))

        declaration.tva_acompte_1 = clean_decimal(request.POST.get("tva_acompte_1"))
        declaration.statut_acompte_1 = request.POST.get("statut_acompte_1")

        declaration.tva_acompte_2 = clean_decimal(request.POST.get("tva_acompte_2"))
        declaration.statut_acompte_2 = request.POST.get("statut_acompte_2")

        declaration.tva_solde = clean_decimal(request.POST.get("tva_solde"))
        declaration.statut_solde = request.POST.get("statut_solde")

        declaration.commentaire_tva_plus_1000 = request.POST.get("commentaire_tva_plus_1000")

        declaration.save()
        messages.success(request, "Déclaration annuelle enregistrée.")
        return redirect(request.path)

    # ----------------------------------------------------
    # 🔢 TOTAL TVA DE L'ANNÉE (A1 + A2 + Solde)
    # ----------------------------------------------------
    total_tva_annee = (
        (declaration.tva_acompte_1 or 0) +
        (declaration.tva_acompte_2 or 0) +
        (declaration.tva_solde or 0)
    )

    return render(request, "tva/tva_saisie_ca12.html", {
        "tca": tca,
        "declaration": declaration,
        "n_1_calcule": n_1_calcule,
        "total_tva_annee": total_tva_annee,  # 🔥 envoyé au template
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from dossiers.models import (
    Client,
    TVAAnnee,
    TVAClientAnnee,
    TVAModule,
    TVADeclaration,
)

# -------------------------
# HISTORIQUE TVA
# -------------------------

@login_required
def tva_historique_client(request, client_id, annee_id):
    # Récupération du client et de l'année TVA
    client = get_object_or_404(Client, id=client_id)
    annee = get_object_or_404(TVAAnnee, id=annee_id)

    # Récupération du module TVA pour ce client et cette année
    tca = TVAClientAnnee.objects.filter(
        client=client,
        annee=annee
    ).select_related("module").first()

    if not tca:
        messages.warning(request, "Aucun module TVA n'est configuré pour cette année.")
        return redirect("client_detail", client.id)

    # Récupération ou création de la déclaration TVA
    declaration, created = TVADeclaration.objects.get_or_create(
        tva_client_annee=tca
    )

    # Type de régime TVA (CA3M, CA3T, CA12, FR, EXO)
    regime = tca.module.type

    contexte_regime = {}

    # -------------------------
    # CA3M (Mensuel)
    # -------------------------
    if regime == "CA3M":
        contexte_regime = {
            "mois": [
                ("Janvier", declaration.tva_janvier, declaration.statut_janvier),
                ("Février", declaration.tva_fevrier, declaration.statut_fevrier),
                ("Mars", declaration.tva_mars, declaration.statut_mars),
                ("Avril", declaration.tva_avril, declaration.statut_avril),
                ("Mai", declaration.tva_mai, declaration.statut_mai),
                ("Juin", declaration.tva_juin, declaration.statut_juin),
                ("Juillet", declaration.tva_juillet, declaration.statut_juillet),
                ("Août", declaration.tva_aout, declaration.statut_aout),
                ("Septembre", declaration.tva_septembre, declaration.statut_septembre),
                ("Octobre", declaration.tva_octobre, declaration.statut_octobre),
                ("Novembre", declaration.tva_novembre, declaration.statut_novembre),
                ("Décembre", declaration.tva_decembre, declaration.statut_decembre),
            ]
        }

    # -------------------------
    # CA3T (Trimestriel)
    # -------------------------
    elif regime == "CA3T":
        contexte_regime = {
            "trimestres": [
                ("T1 (Janv–Mars)", declaration.ca3t_t1, declaration.statut_t1),
                ("T2 (Avr–Juin)", declaration.ca3t_t2, declaration.statut_t2),
                ("T3 (Juil–Sept)", declaration.ca3t_t3, declaration.statut_t3),
                ("T4 (Oct–Déc)", declaration.ca3t_t4, declaration.statut_t4),
            ]
        }

    # -------------------------
    # CA12 (Annuel)
    # -------------------------
    elif regime == "CA12":
        contexte_regime = {
            "annuel": {
                "tva_n_1": declaration.tva_n_1,
                "acompte_1": (declaration.tva_acompte_1, declaration.statut_acompte_1),
                "acompte_2": (declaration.tva_acompte_2, declaration.statut_acompte_2),
                "solde": (declaration.tva_solde, declaration.statut_solde),
                "commentaire": declaration.commentaire_tva_plus_1000,
            }
        }

    # -------------------------
    # EXO / FR (pas de déclaration)
    # -------------------------
    else:
        contexte_regime = {
            "message": "Ce régime TVA ne nécessite pas de déclaration."
        }

    return render(request, "tva/tva_historique_client.html", {
        "client": client,
        "annee": annee,
        "tca": tca,
        "declaration": declaration,
        "regime": regime,
        "contexte_regime": contexte_regime,
    })

# -------------------------
# GESTION TVA
# -------------------------
from dossiers.models import SuiviComptable
from django.contrib.auth.decorators import login_required


@login_required
def tva_gestion_ca3m(request):
    annee_id = request.GET.get("annee")

    if annee_id:
        annee = get_object_or_404(TVAAnnee, id=annee_id)
    else:
        annee = TVAAnnee.objects.order_by("-annee").first()

    tca_list = TVAClientAnnee.objects.filter(
        annee=annee,
        module__type="CA3M"
    ).select_related("client", "module")

    search = request.GET.get("search")
    if search:
        tca_list = tca_list.filter(client__nom__icontains=search)

    # 🔥 Ajout du suivi comptable
    for tca in tca_list:
        tca.suivi = SuiviComptable.objects.filter(
            client=tca.client,
            annee=annee.annee
        ).first()

    return render(request, "tva/gestion/ca3m.html", {
        "annee": annee,
        "annees": TVAAnnee.objects.all().order_by("-annee"),
        "tca_list": tca_list,
    })

from django.contrib.auth.decorators import login_required
from dossiers.models import SuiviComptable

@login_required
def tva_gestion_ca3t(request):
    annee_id = request.GET.get("annee")

    if annee_id:
        annee = get_object_or_404(TVAAnnee, id=annee_id)
    else:
        annee = TVAAnnee.objects.order_by("-annee").first()

    tca_list = TVAClientAnnee.objects.filter(
        annee=annee,
        module__type="CA3T"
    ).select_related("client", "module")

    search = request.GET.get("search")
    if search:
        tca_list = tca_list.filter(
            Q(client__nom__icontains=search) |
            Q(client__numero__icontains=search) |
            Q(client__jour_echeance_tva__icontains=search)
        )

    # 🔥 Ajout du suivi comptable
    for tca in tca_list:
        tca.suivi = SuiviComptable.objects.filter(
            client=tca.client,
            annee=annee.annee
        ).first()

    return render(request, "tva/gestion/ca3t.html", {
        "annee": annee,
        "annees": TVAAnnee.objects.all().order_by("-annee"),
        "tca_list": tca_list,
    })

from django.contrib.auth.decorators import login_required
from dossiers.models import SuiviComptable

@login_required
def tva_gestion_ca12(request):
    # Sélection de l'année
    annee_id = request.GET.get("annee")

    if annee_id:
        annee = get_object_or_404(TVAAnnee, id=annee_id)
    else:
        annee = TVAAnnee.objects.order_by("-annee").first()

    # Tous les clients CA12 pour cette année
    tca_list = TVAClientAnnee.objects.filter(
        annee=annee,
        module__type="CA12"
    ).select_related("client", "module")

    # 🔍 Recherche dynamique
    search = request.GET.get("search")
    if search:
        tca_list = tca_list.filter(
            Q(client__nom__icontains=search) |
            Q(client__numero__icontains=search) |
            Q(client__jour_echeance_tva__icontains=search)
        )

    # 🔥 Ajout du suivi comptable + déclaration CA12 + total TVA année
    for tca in tca_list:

        # Suivi comptable
        tca.suivi = SuiviComptable.objects.filter(
            client=tca.client,
            annee=annee.annee
        ).first()

        # Déclaration CA12
        tca.declaration_obj = TVADeclaration.objects.filter(
            tva_client_annee=tca
        ).first()

        # Total TVA de l'année (A1 + A2 + Solde)
        if tca.declaration_obj:
            tca.total_tva_annee = (
                (tca.declaration_obj.tva_acompte_1 or 0) +
                (tca.declaration_obj.tva_acompte_2 or 0) +
                (tca.declaration_obj.tva_solde or 0)
            )
        else:
            tca.total_tva_annee = 0

    return render(request, "tva/gestion/ca12.html", {
        "annee": annee,
        "annees": TVAAnnee.objects.all().order_by("-annee"),
        "tca_list": tca_list,
    })

from dossiers.models import SuiviComptable
from django.contrib.auth.decorators import login_required


@login_required
def tva_gestion_fr(request):
    # Sélection de l'année
    annee_id = request.GET.get("annee")

    if annee_id:
        annee = get_object_or_404(TVAAnnee, id=annee_id)
    else:
        annee = TVAAnnee.objects.order_by("-annee").first()

    # Tous les clients en Franchise pour cette année
    tca_list = TVAClientAnnee.objects.filter(
        annee=annee,
        module__type="FR"
    ).select_related("client", "module")

    # 🔍 Recherche
    search = request.GET.get("search")
    if search:
        tca_list = tca_list.filter(
            Q(client__nom__icontains=search) |
            Q(client__numero__icontains=search)
        )

    # 🔥 AJOUT ESSENTIEL : suivi comptable
    for tca in tca_list:
        tca.suivi = SuiviComptable.objects.filter(
            client=tca.client,
            annee=annee.annee   # ⚠️ IMPORTANT : pas annee.id
        ).first()

    return render(request, "tva/gestion/fr.html", {
        "annee": annee,
        "annees": TVAAnnee.objects.all().order_by("-annee"),
        "tca_list": tca_list,
    })

from dossiers.models import SuiviComptable
from django.contrib.auth.decorators import login_required

@login_required
def tva_gestion_exo(request):
    # Sélection de l'année
    annee_id = request.GET.get("annee")

    if annee_id:
        annee = get_object_or_404(TVAAnnee, id=annee_id)
    else:
        annee = TVAAnnee.objects.order_by("-annee").first()

    # Tous les clients exonérés pour cette année
    tca_list = TVAClientAnnee.objects.filter(
        annee=annee,
        module__type="EXO"
    ).select_related("client", "module")

    # 🔍 Recherche
    search = request.GET.get("search")
    if search:
        tca_list = tca_list.filter(
            Q(client__nom__icontains=search) |
            Q(client__numero__icontains=search)
        )

    # 🔥 Ajout du suivi comptable
    for tca in tca_list:
        tca.suivi = SuiviComptable.objects.filter(
            client=tca.client,
            annee=annee.annee
        ).first()

    return render(request, "tva/gestion/exo.html", {
        "annee": annee,
        "annees": TVAAnnee.objects.all().order_by("-annee"),
        "tca_list": tca_list,
    })


from django.http import JsonResponse
# ----------------------------------------------------
#   SUIVI COMPTABLE : RESET GLOBAL
# ----------------------------------------------------

@login_required
def reset_suivi_comptable(request, annee):
    if request.method == "POST":
        SuiviComptable.objects.filter(annee=annee).update(
            saisie_en_cours=False,
            saisie_terminee=False
        )
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)


# ----------------------------------------------------
#   MODULE FISCAL
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q

from dossiers.models import Client

from .models import (
    ModuleFiscal,
    AnneeFiscale,
    ClientModuleFiscal,
    ISDeclaration,
)


@login_required
def fiscal_annees(request):
    annees = AnneeFiscale.objects.all().order_by("-annee")

    if request.method == "POST":
        nouvelle_annee = request.POST.get("annee")
        if nouvelle_annee:
            AnneeFiscale.objects.get_or_create(annee=nouvelle_annee)
            messages.success(request, "Année fiscale créée.")
            return redirect("fiscal_annees")

    return render(request, "fiscal/annees.html", {
        "annees": annees,
    })

@login_required
def fiscal_modules(request, annee_id):
    annee = get_object_or_404(AnneeFiscale, id=annee_id)
    modules = ModuleFiscal.objects.all().order_by("nom")

    return render(request, "fiscal/modules.html", {
        "annee": annee,
        "modules": modules,
    })

@login_required
def fiscal_clients_module(request, annee_id, module_id):
    annee = get_object_or_404(AnneeFiscale, id=annee_id)
    module = get_object_or_404(ModuleFiscal, id=module_id)

    # Clients déjà dans le module
    cms = ClientModuleFiscal.objects.filter(
        annee=annee,
        module=module
    ).select_related("client")

    # Tous les clients disponibles
    clients = Client.objects.all().order_by("nom")

    if request.method == "POST":
        client_id = request.POST.get("client_id")
        if client_id:
            client = get_object_or_404(Client, id=client_id)
            ClientModuleFiscal.objects.get_or_create(
                client=client,
                module=module,
                annee=annee
            )
            messages.success(request, "Client ajouté au module.")
            return redirect(request.path)

    return render(request, "fiscal/clients_module.html", {
        "annee": annee,
        "module": module,
        "cms": cms,
        "clients": clients,
    })

@login_required
def fiscal_supprimer_client_module(request, cm_id):
    cm = get_object_or_404(ClientModuleFiscal, id=cm_id)
    annee_id = cm.annee.id
    module_id = cm.module.id

    cm.delete()
    messages.success(request, "Client retiré du module.")

    return redirect("fiscal_clients_module", annee_id=annee_id, module_id=module_id)



# ----------------------------------------------------
#   NOUVEAU MODULE IS
# ----------------------------------------------------

@login_required
def is_saisie(request, client_module_id):
    cm = get_object_or_404(ClientModuleFiscal, id=client_module_id)
    declaration, created = ISDeclaration.objects.get_or_create(client_module=cm)

    def clean_decimal(value):
        if not value or value.strip() == "":
            return 0
        value = value.replace(" ", "").replace(",", ".")
        try:
            return float(value)
        except:
            return 0

    # Pré-remplissage N-2 et N-1
    annee_actuelle = cm.annee.annee
    annee_n_1 = annee_actuelle - 1
    annee_n_2 = annee_actuelle - 2

    prev_1 = ISDeclaration.objects.filter(
        client_module__client=cm.client,
        client_module__annee__annee=annee_n_1
    ).first()

    prev_2 = ISDeclaration.objects.filter(
        client_module__client=cm.client,
        client_module__annee__annee=annee_n_2
    ).first()

    if request.method == "GET":
        if not declaration.is_n_1:
            declaration.is_n_1 = prev_1.total_is() if prev_1 else 0
        if not declaration.is_n_2:
            declaration.is_n_2 = prev_2.total_is() if prev_2 else 0
        declaration.save()

    if request.method == "POST":

        declaration.is_n_2 = clean_decimal(request.POST.get("is_n_2"))
        declaration.is_n_1 = clean_decimal(request.POST.get("is_n_1"))

        for i in range(1, 5):
            declaration.__setattr__(f"acompte_{i}", clean_decimal(request.POST.get(f"acompte_{i}")))
            declaration.__setattr__(f"statut_acompte_{i}", request.POST.get(f"statut_acompte_{i}"))

        declaration.solde = clean_decimal(request.POST.get("solde"))
        declaration.statut_solde = request.POST.get("statut_solde")

        declaration.commentaire_plus_3000 = request.POST.get("commentaire_plus_3000")

        declaration.save()
        messages.success(request, "Déclaration IS enregistrée.")
        return redirect("is_gestion", annee_id=cm.annee.id)

    total_is = declaration.total_is()

    # Construction propre des acomptes pour le template
    acompte_values = []
    for i in range(1, 5):
        acompte_values.append({
            "numero": i,
            "montant": getattr(declaration, f"acompte_{i}", ""),
            "statut": getattr(declaration, f"statut_acompte_{i}", ""),
        })

    return render(request, "is/is_saisie.html", {
        "client_module": cm,
        "declaration": declaration,
        "acompte_values": acompte_values,
        "total_is": total_is,
    })


@login_required
def is_gestion(request, annee_id):
    # Liste des années pour le sélecteur
    annees = AnneeFiscale.objects.order_by("annee")

    # Si l'utilisateur change l'année via GET
    annee_param = request.GET.get("annee")
    if annee_param:
        annee = get_object_or_404(AnneeFiscale, annee=annee_param)
    else:
        annee = get_object_or_404(AnneeFiscale, id=annee_id)

    # Récupération des clients du module IS pour cette année
    cms = ClientModuleFiscal.objects.filter(
        module__nom="IS",
        annee=annee
    ).select_related("client")

    # Ajouter la déclaration IS + calcul du total IS
    for cm in cms:
        cm.declaration, _ = ISDeclaration.objects.get_or_create(client_module=cm)
        d = cm.declaration

        # Calcul du total IS (A1 + A2 + A3 + A4 + Solde)
        total = 0
        for val in [
            d.acompte_1,
            d.acompte_2,
            d.acompte_3,
            d.acompte_4,
            d.solde,
        ]:
            if val:
                total += val

        cm.total_is = total

    return render(request, "is/is_gestion.html", {
        "annee": annee,
        "annees": annees,
        "cms": cms,
    })

# ----------------------------------------------------
#   MODULE CFE
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import CFEDeclaration
from dossiers.models import ClientModuleFiscal, AnneeFiscale

# --- CFE ---
from .models import CFEDeclaration

@login_required
def cfe_gestion(request, annee_id):
    annees = AnneeFiscale.objects.order_by("annee")

    annee_param = request.GET.get("annee")
    if annee_param:
        annee = get_object_or_404(AnneeFiscale, annee=annee_param)
    else:
        annee = get_object_or_404(AnneeFiscale, id=annee_id)

    cms = ClientModuleFiscal.objects.filter(
        module__nom="CFE",
        annee=annee
    ).select_related("client")

    for cm in cms:
        cm.declaration, _ = CFEDeclaration.objects.get_or_create(client_module=cm)
        d = cm.declaration
        cm.total_cfe = (d.acompte_cfe or 0) + (d.solde_cfe or 0)

    return render(request, "cfe/cfe_gestion.html", {
        "annee": annee,
        "annees": annees,
        "cms": cms,
    })

@login_required
def cfe_saisie(request, client_module_id):
    cm = get_object_or_404(ClientModuleFiscal, id=client_module_id)
    declaration, created = CFEDeclaration.objects.get_or_create(client_module=cm)

    # Pré-remplissage CFE N-1
    if created:
        try:
            annee_precedente = AnneeFiscale.objects.get(annee=cm.annee.annee - 1)
            cm_prec = ClientModuleFiscal.objects.get(
                client=cm.client,
                module__nom="CFE",
                annee=annee_precedente
            )
            decl_prec = CFEDeclaration.objects.get(client_module=cm_prec)
            declaration.cfe_n_1 = decl_prec.total_cfe
        except:
            declaration.cfe_n_1 = 0

        declaration.save()

    # Fonction utilitaire interne
    def to_decimal(value):
        if not value:
            return 0
        return value.replace(",", ".")

    # Traitement POST
    if request.method == "POST":
        declaration.cfe_n_1 = to_decimal(request.POST.get("cfe_n_1"))
        declaration.acompte_cfe = to_decimal(request.POST.get("acompte_cfe"))
        declaration.solde_cfe = to_decimal(request.POST.get("solde_cfe"))

        declaration.statut_acompte = request.POST.get("statut_acompte")
        declaration.statut_solde = request.POST.get("statut_solde")
        declaration.mode_paiement = request.POST.get("mode_paiement", "")
        declaration.degrevement = request.POST.get("degrevement", "")
        declaration.formulaire_1447c = request.POST.get("formulaire_1447c", "")
        declaration.statut_1447c = request.POST.get("statut_1447c")
        declaration.commentaire_plus_3000 = request.POST.get("commentaire_plus_3000", "")

        declaration.save()
        messages.success(request, "Déclaration CFE enregistrée avec succès.")
        return redirect("cfe_gestion", annee_id=cm.annee.id)

    # Affichage GET
    return render(request, "cfe/cfe_saisie.html", {
        "client_module": cm,
        "declaration": declaration,
    })


# ----------------------------------------------------
#   MODULE CVAE
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from .models import CVAEDeclaration, ClientModuleFiscal, AnneeFiscale
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages

@login_required
def cvae_saisie(request, client_module_id):
    cm = get_object_or_404(ClientModuleFiscal, id=client_module_id)
    declaration, created = CVAEDeclaration.objects.get_or_create(client_module=cm)

    # Pré-remplissage CVAE N-1
    if created and declaration.cvae_n_1 == 0:
        try:
            annee_precedente = AnneeFiscale.objects.get(annee=cm.annee.annee - 1)
            cm_prec = ClientModuleFiscal.objects.get(
                client=cm.client,
                module__nom="CVAE",
                annee=annee_precedente
            )
            decl_prec = CVAEDeclaration.objects.get(client_module=cm_prec)
            declaration.cvae_n_1 = decl_prec.total_cvae()
            declaration.save()
        except:
            pass

    def to_decimal(value):
        if not value:
            return 0
        return value.replace(",", ".")

    if request.method == "POST":
        declaration.cvae_n_1 = to_decimal(request.POST.get("cvae_n_1"))
        declaration.acompte_cvae = to_decimal(request.POST.get("acompte_cvae"))
        declaration.solde_cvae = to_decimal(request.POST.get("solde_cvae"))

        declaration.statut_acompte_cvae = request.POST.get("statut_acompte_cvae")
        declaration.statut_solde_cvae = request.POST.get("statut_solde_cvae")
        declaration.commentaire_plus_1500 = request.POST.get("commentaire_plus_1500", "")

        declaration.save()
        messages.success(request, "Déclaration CVAE enregistrée avec succès.")
        return redirect("cvae_gestion", annee_id=cm.annee.id)

    total_cvae = declaration.total_cvae()

    return render(request, "cvae/cvae_saisie.html", {
        "client_module": cm,
        "declaration": declaration,
        "total_cvae": total_cvae,
    })

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch

@login_required
def cvae_gestion(request, annee_id):
    annee = get_object_or_404(AnneeFiscale, id=annee_id)
    annees = AnneeFiscale.objects.all().order_by("-annee")

    cms = (
        ClientModuleFiscal.objects
        .filter(annee=annee, module__nom="CVAE")
        .select_related("client", "annee")
        .prefetch_related("cvae_declaration")
    )

    # On s’assure que chaque cm a une déclaration
    for cm in cms:
        if not hasattr(cm, "cvae_declaration"):
            cm.cvae_declaration, _ = CVAEDeclaration.objects.get_or_create(client_module=cm)

    return render(request, "cvae/cvae_gestion.html", {
        "annee": annee,
        "annees": annees,
        "cms": cms,
    })

# ----------------------------------------------------
#   MODULE TVS
# ----------------------------------------------------

@login_required
def tvs_saisie(request, client_module_id):
    cm = get_object_or_404(ClientModuleFiscal, id=client_module_id)
    declaration, created = TVSDeclaration.objects.get_or_create(client_module=cm)

    # Pré-remplissage TVS N-1
    if created and declaration.tvs_n_1 == 0:
        try:
            annee_prec = AnneeFiscale.objects.get(annee=cm.annee.annee - 1)
            cm_prec = ClientModuleFiscal.objects.get(
                client=cm.client,
                module__nom="TVS",
                annee=annee_prec
            )
            decl_prec = TVSDeclaration.objects.get(client_module=cm_prec)
            declaration.tvs_n_1 = decl_prec.montant
            declaration.save()
        except:
            pass

    def to_decimal(value):
        if not value:
            return 0
        return value.replace(",", ".")

    if request.method == "POST":
        declaration.tvs_n_1 = to_decimal(request.POST.get("tvs_n_1"))
        declaration.vehicule = "vehicule" in request.POST
        declaration.soumis_tvs_n = "soumis_tvs_n" in request.POST

        declaration.formulaire = request.POST.get("formulaire")
        declaration.montant = to_decimal(request.POST.get("montant"))

        declaration.statut_tvs = request.POST.get("statut_tvs")
        declaration.info_vehicule = request.POST.get("info_vehicule")

        declaration.date_achat = request.POST.get("date_achat") or None
        declaration.date_cession = request.POST.get("date_cession") or None

        declaration.save()
        messages.success(request, "Déclaration TVS enregistrée avec succès.")
        return redirect("tvs_gestion", annee_id=cm.annee.id)

    return render(request, "tvs/tvs_saisie.html", {
        "client_module": cm,
        "declaration": declaration,
    })

@login_required
def tvs_gestion(request, annee_id):
    annee = get_object_or_404(AnneeFiscale, id=annee_id)
    annees = AnneeFiscale.objects.all().order_by("-annee")

    cms = (
        ClientModuleFiscal.objects
        .filter(annee=annee, module__nom="TVS")
        .select_related("client", "annee")
        .prefetch_related("tvs_declaration")
    )

    for cm in cms:
        if not hasattr(cm, "tvs_declaration"):
            cm.tvs_declaration, _ = TVSDeclaration.objects.get_or_create(client_module=cm)

    return render(request, "tvs/tvs_gestion.html", {
        "annee": annee,
        "annees": annees,
        "cms": cms,
    })


# ----------------------------------------------------
#   MODULE DESDEB
# ----------------------------------------------------

@login_required
def desdeb_saisie(request, client_module_id):
    cm = get_object_or_404(ClientModuleFiscal, id=client_module_id)
    declaration, created = DESDEBDeclaration.objects.get_or_create(client_module=cm)

    # Liste des mois + labels
    mois_labels = {
        "janvier": "Janvier (10/02)",
        "fevrier": "Février (10/03)",
        "mars": "Mars (10/04)",
        "avril": "Avril (10/05)",
        "mai": "Mai (10/06)",
        "juin": "Juin (10/07)",
        "juillet": "Juillet (10/08)",
        "aout": "Août (10/09)",
        "septembre": "Septembre (10/10)",
        "octobre": "Octobre (10/11)",
        "novembre": "Novembre (10/12)",
        "decembre": "Décembre (10/01)",
    }

    if request.method == "POST":
        declaration.responsable = request.POST.get("responsable")
        declaration.retour_client = request.POST.get("retour_client")

        # Mise à jour des 12 mois
        for mois in mois_labels.keys():
            setattr(declaration, f"ref_{mois}", request.POST.get(f"ref_{mois}"))
            setattr(declaration, f"statut_{mois}", request.POST.get(f"statut_{mois}"))

        declaration.save()
        messages.success(request, "Déclaration DESDEB enregistrée avec succès.")
        return redirect("desdeb_gestion", annee_id=cm.annee.id)

    # Construction du dictionnaire pour le template
    mois_data = {}
    for mois, label in mois_labels.items():
        mois_data[mois] = {
            "label": label,
            "ref": getattr(declaration, f"ref_{mois}"),
            "statut": getattr(declaration, f"statut_{mois}"),
        }

    return render(request, "desdeb/desdeb_saisie.html", {
        "client_module": cm,
        "declaration": declaration,
        "mois_data": mois_data,
    })

@login_required
def desdeb_gestion(request, annee_id):
    annee = get_object_or_404(AnneeFiscale, id=annee_id)
    annees = AnneeFiscale.objects.all().order_by("-annee")

    cms = (
        ClientModuleFiscal.objects
        .filter(annee=annee, module__nom="DESDEB")
        .select_related("client", "annee")
        .prefetch_related("desdeclaration")
    )

    # Labels des mois
    mois_labels = {
        "janvier": "Janvier",
        "fevrier": "Février",
        "mars": "Mars",
        "avril": "Avril",
        "mai": "Mai",
        "juin": "Juin",
        "juillet": "Juillet",
        "aout": "Août",
        "septembre": "Septembre",
        "octobre": "Octobre",
        "novembre": "Novembre",
        "decembre": "Décembre",
    }

    # On prépare les données pour chaque client
    for cm in cms:
        if not hasattr(cm, "desdeclaration"):
            cm.desdeclaration, _ = DESDEBDeclaration.objects.get_or_create(client_module=cm)

        decl = cm.desdeclaration

        mois_data = {}
        for mois, label in mois_labels.items():
            mois_data[mois] = {
                "label": label,
                "ref": getattr(decl, f"ref_{mois}"),
                "statut": getattr(decl, f"statut_{mois}"),
            }

        cm.mois_data = mois_data

    return render(request, "desdeb/desdeb_gestion.html", {
        "annee": annee,
        "annees": annees,
        "cms": cms,
        "mois_labels": mois_labels,
    })


# ----------------------------------------------------
#   MODULE DIVIDENDES
# ----------------------------------------------------

@login_required
def dividendes_saisie(request, client_module_id):
    cm = get_object_or_404(ClientModuleFiscal, id=client_module_id)
    declaration, created = DividendesDeclaration.objects.get_or_create(client_module=cm)

    def to_decimal(value):
        if not value:
            return 0
        return value.replace(",", ".")

    if request.method == "POST":
        declaration.nom = request.POST.get("nom")
        declaration.montant = to_decimal(request.POST.get("montant"))

        declaration.date_paiement = request.POST.get("date_paiement") or None
        declaration.date_2777d = request.POST.get("date_2777d") or None
        declaration.date_2561 = request.POST.get("date_2561") or None

        declaration.annee_versement = request.POST.get("annee_versement")
        declaration.commentaires = request.POST.get("commentaires")

        declaration.statut_dividendes = request.POST.get("statut_dividendes")

        declaration.save()
        messages.success(request, "Déclaration Dividendes enregistrée avec succès.")
        return redirect("dividendes_gestion", annee_id=cm.annee.id)

    return render(request, "dividendes/dividendes_saisie.html", {
        "client_module": cm,
        "declaration": declaration,
    })

@login_required
def dividendes_gestion(request, annee_id):
    annee = get_object_or_404(AnneeFiscale, id=annee_id)
    annees = AnneeFiscale.objects.all().order_by("-annee")

    cms = (
        ClientModuleFiscal.objects
        .filter(annee=annee, module__nom="Dividendes")
        .select_related("client", "annee")
        .prefetch_related("dividendes_declaration")
    )

    for cm in cms:
        if not hasattr(cm, "dividendes_declaration"):
            cm.dividendes_declaration, _ = DividendesDeclaration.objects.get_or_create(client_module=cm)

    return render(request, "dividendes/dividendes_gestion.html", {
        "annee": annee,
        "annees": annees,
        "cms": cms,
    })


# ----------------------------------------------------
#   MODULE DP
# ----------------------------------------------------

@login_required
def dp_saisie(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    declaration, created = DPDeclaration.objects.get_or_create(client=client)

    if request.method == "POST":
        declaration.dossier_deontologie = request.POST.get("dossier_deontologie")
        declaration.acceptation_lab = request.POST.get("acceptation_lab")
        declaration.piece_identite = request.POST.get("piece_identite")
        declaration.statut = request.POST.get("statut")
        declaration.bail = request.POST.get("bail")
        declaration.lettre_mission = request.POST.get("lettre_mission")
        declaration.avenant = request.POST.get("avenant")

        declaration.save()
        messages.success(request, "Dossier DP enregistré avec succès.")
        return redirect("dp_gestion")

    return render(request, "dp/dp_saisie.html", {
        "client": client,
        "declaration": declaration,
    })

@login_required
def dp_gestion(request):
    clients = Client.objects.all().order_by("nom")

    for client in clients:
        if not hasattr(client, "dp"):
            client.dp, _ = DPDeclaration.objects.get_or_create(client=client)

    return render(request, "dp/dp_gestion.html", {
        "clients": clients,
    })

# ----------------------------------------------------
#   LOGIN
# ----------------------------------------------------

from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.shortcuts import redirect

class CustomLoginView(LoginView):
    template_name = "auth/login.html"

    def get_success_url(self):
        user = self.request.user

        # Staff + Admin
        if user.is_staff or user.is_superuser:
            return reverse_lazy("user_space")

        # Client
        if user.groups.filter(name__iexact="client").exists():
            return reverse_lazy("paie:paie_client_dashboard")

        # Partenaire
        if user.groups.filter(name__iexact="partenaire").exists():
            return reverse_lazy("paie:partenaire_dashboard")
       
        # Fallback
        return reverse_lazy("user_space")

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "auth/register.html"
    success_url = reverse_lazy("login")


def logout_view(request):
    logout(request)
    return redirect("login")

# ----------------------------------------------------
#   ESPACE UTILISATEUR
# ----------------------------------------------------

from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import (
    UserNote, Todo, Client, SuiviComptable,
    TVAAnnee, TVAModule, TVAClientAnnee, TVADeclaration
)


@login_required
def user_space(request):
    user = request.user
    today = date.today()
    current_year = today.year

    # ----------------------------------------------------
    # 1) NOTES & TÂCHES
    # ----------------------------------------------------
    last_notes = UserNote.objects.filter(user=user).order_by('-created_at')[:3]
    last_todos = Todo.objects.filter(user=user).order_by('-created_at')[:3]

    reminders_today = Todo.objects.filter(
        user=user,
        reminder_date__date=today,
        done=False
    ).order_by("reminder_date")

    # ----------------------------------------------------
    # 2) KPIs COMPTABILITÉ (ANNÉE EN COURS)
    # ----------------------------------------------------

    # Clients concernés : périodicité mensuel / régulier
    clients_concernes_qs = Client.objects.filter(
        periodicite__in=["MENSUEL", "REGULIER"]
    )
    kpi_total_clients = clients_concernes_qs.count()

    # Suivi comptable pour l'année en cours
    suivis_qs = SuiviComptable.objects.filter(
        annee=current_year,
        client__in=clients_concernes_qs
    )

    kpi_terminees = suivis_qs.filter(saisie_terminee=True).count()
    kpi_en_cours = suivis_qs.filter(saisie_en_cours=True, saisie_terminee=False).count()

    # Non commencée
    kpi_non_commencees = kpi_total_clients - kpi_terminees - kpi_en_cours
    if kpi_non_commencees < 0:
        kpi_non_commencees = 0

    # Pourcentage
    kpi_pourcentage_terminees = (
        round((kpi_terminees / kpi_total_clients) * 100, 1)
        if kpi_total_clients > 0 else 0
    )

    # ----------------------------------------------------
    # 3) KPIs CA3M (SUIVI COMPTABLE)
    # ----------------------------------------------------
    total_ca3m = 0
    ca3m_terminees = 0
    ca3m_en_cours = 0
    ca3m_non_commencees = 0
    ca3m_pourcentage_terminees = 0

    try:
        tva_annee = TVAAnnee.objects.get(annee=current_year)
        module_ca3m = TVAModule.objects.get(annee=tva_annee, type="CA3M")

        clients_ca3m_qs = TVAClientAnnee.objects.filter(
            annee=tva_annee,
            module=module_ca3m
        )

        total_ca3m = clients_ca3m_qs.count()

        suivis_ca3m = SuiviComptable.objects.filter(
            annee=current_year,
            client__in=clients_ca3m_qs.values("client")
        )

        ca3m_terminees = suivis_ca3m.filter(saisie_terminee=True).count()
        ca3m_en_cours = suivis_ca3m.filter(
            saisie_en_cours=True,
            saisie_terminee=False
        ).count()

        ca3m_non_commencees = total_ca3m - ca3m_terminees - ca3m_en_cours
        if ca3m_non_commencees < 0:
            ca3m_non_commencees = 0

        ca3m_pourcentage_terminees = (
            round((ca3m_terminees / total_ca3m) * 100, 1)
            if total_ca3m > 0 else 0
        )

    except (TVAAnnee.DoesNotExist, TVAModule.DoesNotExist):
        pass

    # ----------------------------------------------------
    # 4) KPIs TVA (STATUT DU MOIS PRÉCÉDENT STRICT)
    # ----------------------------------------------------

    # Déterminer le mois TVA à analyser
    if today.month == 1:
        tva_year = current_year - 1
        tva_month = 12
    else:
        tva_year = current_year
        tva_month = today.month - 1

    mois_map = {
        1: "janvier",
        2: "fevrier",
        3: "mars",
        4: "avril",
        5: "mai",
        6: "juin",
        7: "juillet",
        8: "aout",
        9: "septembre",
        10: "octobre",
        11: "novembre",
        12: "decembre",
    }

    mois_label = mois_map[tva_month]
    champ_statut = f"statut_{mois_label}"

    # Initialisation
    tva_acceptes = 0
    tva_teletransmis = 0
    tva_a_envoyer = 0
    tva_sans_pastille = 0
    tva_rejetes = 0

    try:
        tva_annee = TVAAnnee.objects.get(annee=tva_year)
        module_ca3m = TVAModule.objects.get(annee=tva_annee, type="CA3M")

        clients_ca3m_qs = TVAClientAnnee.objects.filter(
            annee=tva_annee,
            module=module_ca3m
        )

        declarations = TVADeclaration.objects.filter(
            tva_client_annee__in=clients_ca3m_qs
        )

        for decl in declarations:
            statut = getattr(decl, champ_statut, "NONE") or "NONE"

            if statut == "VERT_FONCE":
                tva_acceptes += 1
            elif statut == "VERT_CLAIR":
                tva_teletransmis += 1
            elif statut == "JAUNE":
                tva_a_envoyer += 1
            elif statut == "BLANC":
                tva_rejetes += 1
            else:
                tva_sans_pastille += 1

        def pct(val):
            return round((val / total_ca3m) * 100, 1) if total_ca3m > 0 else 0

        pct_acceptes = pct(tva_acceptes)
        pct_teletransmis = pct(tva_teletransmis)
        pct_a_envoyer = pct(tva_a_envoyer)
        pct_sans_pastille = pct(tva_sans_pastille)
        pct_rejetes = pct(tva_rejetes)

    except (TVAAnnee.DoesNotExist, TVAModule.DoesNotExist):
        pct_acceptes = pct_teletransmis = pct_a_envoyer = pct_sans_pastille = pct_rejetes = 0

    # ----------------------------------------------------
    # 5) RENDER
    # ----------------------------------------------------
    return render(request, "user_space/dashboard.html", {
        "user": user,

        # Notes & tâches
        "last_notes": last_notes,
        "last_todos": last_todos,
        "reminders_today": reminders_today,

        # Comptabilité
        "kpi_total_clients": kpi_total_clients,
        "kpi_terminees": kpi_terminees,
        "kpi_en_cours": kpi_en_cours,
        "kpi_non_commencees": kpi_non_commencees,
        "kpi_pourcentage_terminees": kpi_pourcentage_terminees,

        # CA3M (saisie comptable)
        "total_ca3m": total_ca3m,
        "ca3m_terminees": ca3m_terminees,
        "ca3m_en_cours": ca3m_en_cours,
        "ca3m_non_commencees": ca3m_non_commencees,
        "ca3m_pourcentage_terminees": ca3m_pourcentage_terminees,

        # TVA
        "tva_month_label": mois_label.capitalize(),
        "tva_acceptes": tva_acceptes,
        "tva_teletransmis": tva_teletransmis,
        "tva_a_envoyer": tva_a_envoyer,
        "tva_sans_pastille": tva_sans_pastille,
        "tva_rejetes": tva_rejetes,

        "pct_acceptes": pct_acceptes,
        "pct_teletransmis": pct_teletransmis,
        "pct_a_envoyer": pct_a_envoyer,
        "pct_sans_pastille": pct_sans_pastille,
        "pct_rejetes": pct_rejetes,
    })


# ----------------------------------------------------
#   NOTES CLIENTS
# ----------------------------------------------------

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Client, ClientNote

from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

@login_required
def client_notes(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    # Notes filtrées par utilisateur
    notes = ClientNote.objects.filter(
        client=client,
        user=request.user
    ).order_by("-created_at")

    # Tags & catégories du client
    tags = NoteTag.objects.filter(client=client)
    categories = NoteCategorie.objects.filter(client=client)

    # Année actuelle pour le bouton "Suivi comptable"
    current_year = now().year

    # Création d'une nouvelle note
    if request.method == "POST":
        contenu = request.POST.get("contenu")
        categorie_id = request.POST.get("categorie")
        tags_ids = request.POST.getlist("tags")

        if contenu:
            note = ClientNote.objects.create(
                user=request.user,
                client=client,
                contenu=contenu,
                categorie_id=categorie_id if categorie_id else None
            )
            note.tags.set(tags_ids)

        return redirect("client_notes", client_id=client.id)

    return render(request, "notes/client_notes_page.html", {
        "client": client,
        "notes": notes,
        "tags": tags,
        "categories": categories,
        "current_year": current_year,   # 🔥 indispensable pour ton bouton
    })

@login_required
def edit_note(request, note_id):
    note = get_object_or_404(ClientNote, id=note_id, user=request.user)
    client = note.client

    tags = NoteTag.objects.filter(client=client)
    categories = NoteCategorie.objects.filter(client=client)

    if request.method == "POST":
        note.contenu = request.POST.get("contenu")
        note.categorie_id = request.POST.get("categorie") or None
        note.tags.set(request.POST.getlist("tags"))
        note.save()

        return redirect("client_notes", client_id=client.id)

    return render(request, "notes/edit_note.html", {
        "note": note,
        "tags": tags,
        "categories": categories,
    })

@login_required
def delete_note(request, note_id):
    note = get_object_or_404(ClientNote, id=note_id, user=request.user)
    client_id = note.client.id
    note.delete()
    return redirect("client_notes", client_id=client_id)

@login_required
def add_tag(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == "POST":
        nom = request.POST.get("nom")
        if nom:
            NoteTag.objects.create(client=client, nom=nom)

    return redirect("client_notes", client_id=client.id)

@login_required
def add_categorie(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == "POST":
        nom = request.POST.get("nom")
        if nom:
            NoteCategorie.objects.create(client=client, nom=nom)

    return redirect("client_notes", client_id=client.id)


@login_required
def delete_tag(request, tag_id):
    tag = get_object_or_404(NoteTag, id=tag_id)
    client_id = tag.client.id
    tag.delete()
    return redirect("client_notes", client_id=client_id)

@login_required
def delete_categorie(request, cat_id):
    cat = get_object_or_404(NoteCategorie, id=cat_id)
    client_id = cat.client.id
    cat.delete()
    return redirect("client_notes", client_id=client_id)



# ----------------------------------------------------
#   NOTES PERSONNELLES
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import UserNote, UserNoteCategorie

@login_required
def add_user_note_categorie(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        if nom:
            UserNoteCategorie.objects.create(
                user=request.user,
                nom=nom
            )
        return redirect("add_user_note")  # retour au formulaire de note

    return render(request, "dossiers/add_user_note_categorie.html")


@login_required
def user_notes(request):
    notes = UserNote.objects.filter(user=request.user)

    # Filtre texte
    search = request.GET.get("search")
    if search:
        notes = notes.filter(
            Q(titre__icontains=search) |
            Q(contenu__icontains=search)
        )

    # Filtre catégorie
    categorie_id = request.GET.get("categorie")
    if categorie_id:
        notes = notes.filter(categorie_id=categorie_id)

    categories = UserNoteCategorie.objects.filter(user=request.user)

    notes = notes.order_by("-created_at")

    return render(request, "dossiers/user_notes_list.html", {
        "notes": notes,
        "categories": categories,
        "search": search,
        "categorie_id": categorie_id,
    })


@login_required
def add_user_note(request):
    categories = UserNoteCategorie.objects.filter(user=request.user)

    # Soumission du formulaire "Nouvelle catégorie"
    if request.method == "POST" and "new_category" in request.POST:
        nom = request.POST.get("nom_categorie")
        if nom:
            UserNoteCategorie.objects.create(user=request.user, nom=nom)
        return redirect("add_user_note")

    # Soumission du formulaire "Nouvelle note"
    if request.method == "POST" and "new_note" in request.POST:
        titre = request.POST.get("titre")
        contenu = request.POST.get("contenu")
        categorie_id = request.POST.get("categorie")

        if contenu:
            UserNote.objects.create(
                user=request.user,
                titre=titre,
                contenu=contenu,
                categorie_id=categorie_id if categorie_id else None
            )
        return redirect("user_notes")

    return render(request, "dossiers/add_user_note.html", {
        "categories": categories,
    })

@login_required
def edit_user_note(request, note_id):
    note = get_object_or_404(UserNote, id=note_id, user=request.user)
    categories = UserNoteCategorie.objects.filter(user=request.user)

    if request.method == "POST":
        note.titre = request.POST.get("titre")
        note.contenu = request.POST.get("contenu")
        note.categorie_id = request.POST.get("categorie") or None
        note.save()
        return redirect("user_notes")

    return render(request, "dossiers/edit_user_note.html", {
        "note": note,
        "categories": categories,
    })

@login_required
def delete_user_note(request, note_id):
    note = get_object_or_404(UserNote, id=note_id, user=request.user)
    note.delete()
    return redirect("user_notes")

# ----------------------------------------------------
#   MODULE KANBAN
# ----------------------------------------------------


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models  

@login_required
def kanban_board(request):
    # Colonnes triées
    columns = KanbanColumn.objects.filter(user=request.user).order_by("position")

    # Cartes triées
    cards = KanbanCard.objects.filter(user=request.user).order_by("position")

    # Tous les tags de l'utilisateur
    tags = KanbanTag.objects.filter(user=request.user).order_by("name")

    # Ajouter la liste des tags associés à chaque carte
    for card in cards:
        card.tags = [ct.tag for ct in card.kanbancardtag_set.all()]

    return render(request, "dossiers/kanban_board.html", {
        "columns": columns,
        "cards": cards,
        "tags": tags,
    })


@login_required
def add_kanban_column(request):
    if request.method == "POST":
        title = request.POST.get("title")
        color = request.POST.get("color", "#cccccc")

        if title:
            max_pos = KanbanColumn.objects.filter(user=request.user).aggregate(models.Max("position"))["position__max"] or 0
            KanbanColumn.objects.create(
                user=request.user,
                title=title,
                color=color,
                position=max_pos + 1
            )

        return redirect("kanban_board")

@login_required
def rename_kanban_column(request, column_id):
    column = get_object_or_404(KanbanColumn, id=column_id, user=request.user)

    if request.method == "POST":
        new_title = request.POST.get("title")
        if new_title:
            column.title = new_title
            column.save()
        return redirect("kanban_board")

@login_required
def change_kanban_column_color(request, column_id):
    column = get_object_or_404(KanbanColumn, id=column_id, user=request.user)

    if request.method == "POST":
        new_color = request.POST.get("color")
        if new_color:
            column.color = new_color
            column.save()
        return redirect("kanban_board")


@login_required
def delete_kanban_column(request, column_id):
    column = get_object_or_404(KanbanColumn, id=column_id, user=request.user)
    column.delete()
    return redirect("kanban_board")

import json

@login_required
def move_kanban_column(request, column_id=None):
    if request.method == "POST":
        data = json.loads(request.body)

        for item in data:
            col = KanbanColumn.objects.filter(id=item["id"], user=request.user).first()
            if col:
                col.position = item["position"]
                col.save()

        return JsonResponse({"status": "ok"})

@login_required
def add_kanban_card(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        column_id = request.POST.get("column_id")

        column = get_object_or_404(KanbanColumn, id=column_id, user=request.user)

        max_pos = KanbanCard.objects.filter(column=column).aggregate(models.Max("position"))["position__max"] or 0

        KanbanCard.objects.create(
            user=request.user,
            column=column,
            title=title,
            description=description,
            position=max_pos + 1
        )

        return redirect("kanban_board")


@login_required
def edit_kanban_card(request, card_id):
    card = get_object_or_404(KanbanCard, id=card_id, user=request.user)

    if request.method == "POST":
        card.title = request.POST.get("title")
        card.description = request.POST.get("description")
        card.save()
        return redirect("kanban_board")

    # GET → afficher le formulaire
    return render(request, "dossiers/edit_kanban_card.html", {
        "card": card,
    })

@login_required
def delete_kanban_card(request, card_id):
    card = get_object_or_404(KanbanCard, id=card_id, user=request.user)
    card.delete()
    return redirect("kanban_board")

@login_required
def move_kanban_card(request):
    data = json.loads(request.body)

    card = KanbanCard.objects.filter(id=data["card_id"], user=request.user).first()
    new_column = KanbanColumn.objects.filter(id=data["column_id"], user=request.user).first()

    if card and new_column:
        card.column = new_column
        card.position = data["position"]
        card.save()

    return JsonResponse({"status": "ok"})

@login_required
def add_kanban_tag(request):
    if request.method == "POST":
        name = request.POST.get("name")
        color = request.POST.get("color", "#888888")

        if name:
            KanbanTag.objects.create(
                user=request.user,
                name=name,
                color=color
            )

        return redirect("kanban_board")

@login_required
def edit_kanban_tag(request, tag_id):
    tag = get_object_or_404(KanbanTag, id=tag_id, user=request.user)

    if request.method == "POST":
        tag.name = request.POST.get("name")
        tag.color = request.POST.get("color")
        tag.save()
        return redirect("kanban_board")

@login_required
def delete_kanban_tag(request, tag_id):
    tag = get_object_or_404(KanbanTag, id=tag_id, user=request.user)
    tag.delete()
    return redirect("kanban_board")

@login_required
def kanban_tags(request):
    if request.method == "POST":
        name = request.POST.get("name")
        color = request.POST.get("color")

        if name:
            KanbanTag.objects.create(
                user=request.user,
                name=name,
                color=color or "#cccccc"
            )

    # Que ce soit GET (accès direct) ou POST, on revient au Kanban
    return redirect("kanban_board")

@login_required
def edit_kanban_tag(request, tag_id):
    tag = get_object_or_404(KanbanTag, id=tag_id, user=request.user)

    if request.method == "POST":
        tag.name = request.POST.get("name")
        tag.color = request.POST.get("color")
        tag.save()
        return redirect("kanban_tags")

    return render(request, "dossiers/edit_kanban_tag.html", {
        "tag": tag,
    })

@login_required
def delete_kanban_tag(request, tag_id):
    tag = get_object_or_404(KanbanTag, id=tag_id, user=request.user)
    tag.delete()
    return redirect("kanban_tags")

from django.http import JsonResponse
import json

@login_required
def assign_tag_to_card(request):
    data = json.loads(request.body)

    card_id = data.get("card_id")
    tag_id = data.get("tag_id")

    card = KanbanCard.objects.filter(id=card_id, user=request.user).first()
    tag = KanbanTag.objects.filter(id=tag_id, user=request.user).first()

    if card and tag:
        KanbanCardTag.objects.get_or_create(card=card, tag=tag)
        return JsonResponse({"status": "ok"})

    return JsonResponse({"status": "error"}, status=400)


@login_required
def remove_tag_from_card(request):
    data = json.loads(request.body)

    card_id = data.get("card_id")
    tag_id = data.get("tag_id")

    KanbanCardTag.objects.filter(
        card_id=card_id,
        tag_id=tag_id,
        card__user=request.user
    ).delete()

    return JsonResponse({"status": "ok"})

# ----------------------------------------------------
#   TO DO LIST
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import date, timedelta
from .models import Todo, SubTask

@login_required
def todo_list(request):
    user = request.user
    today = date.today()
    tomorrow = today + timedelta(days=1)

    todos = Todo.objects.filter(user=user).order_by('due_date', 'priority')

    context = {
        "today_tasks": todos.filter(due_date=today, done=False),
        "tomorrow_tasks": todos.filter(due_date=tomorrow, done=False),
        "upcoming_tasks": todos.filter(due_date__gt=tomorrow, done=False),
        "no_date_tasks": todos.filter(due_date__isnull=True, done=False),
        "overdue_tasks": todos.filter(due_date__lt=today, done=False),
        "completed_tasks": todos.filter(done=True).order_by('-completed_at'),
    }

    return render(request, "todo/todo_list.html", context)

@login_required
def todo_add(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description", "")
        priority = request.POST.get("priority", "normal")
        due_date = request.POST.get("due_date") or None
        reminder_date = request.POST.get("reminder_date") or None

        recurrence_type = request.POST.get("recurrence_type", "none")
        recurrence_day = request.POST.get("recurrence_day") or None

        Todo.objects.create(
            user=request.user,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            reminder_date=reminder_date,
            recurrence_type=recurrence_type,
            recurrence_day=recurrence_day,
        )

        return redirect("todo_list")

    return redirect("todo_list")

@login_required
def todo_edit(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)

    if request.method == "POST":
        todo.title = request.POST.get("title")
        todo.description = request.POST.get("description", "")
        todo.priority = request.POST.get("priority", "normal")
        todo.due_date = request.POST.get("due_date") or None
        todo.reminder_date = request.POST.get("reminder_date") or None
        todo.save()

        return redirect("todo_list")

    return render(request, "todo/todo_edit.html", {"todo": todo})

from dateutil.relativedelta import relativedelta
import calendar

@login_required
def todo_toggle(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)

    todo.done = not todo.done

    if todo.done:
        todo.completed_at = timezone.now()

        # -----------------------------------------
        #   GÉNÉRATION DE LA PROCHAINE TÂCHE
        # -----------------------------------------
        if todo.recurrence_type != "none" and todo.due_date:

            # 1) Tous les 1er du mois
            if todo.recurrence_type == "monthly_first":
                next_due = (todo.due_date + relativedelta(months=1)).replace(day=1)

            # 2) Tous les mois le jour choisi
            elif todo.recurrence_type == "monthly_day":
                day = int(todo.recurrence_day or todo.due_date.day)
                next_month = todo.due_date + relativedelta(months=1)

                # On ajuste si le mois n'a pas assez de jours
                last_day = calendar.monthrange(next_month.year, next_month.month)[1]
                next_due = next_month.replace(day=min(day, last_day))

            # Création de la nouvelle tâche
            Todo.objects.create(
                user=todo.user,
                title=todo.title,
                description=todo.description,
                priority=todo.priority,
                due_date=next_due,
                recurrence_type=todo.recurrence_type,
                recurrence_day=todo.recurrence_day,
            )

    else:
        todo.completed_at = None

    todo.save()
    return redirect("todo_list")

@login_required
def todo_delete(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)
    todo.delete()
    return redirect("todo_list")

@login_required
def subtask_add(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)

    if request.method == "POST":
        title = request.POST.get("title")
        SubTask.objects.create(todo=todo, title=title)

    return redirect("todo_list")

@login_required
def subtask_toggle(request, subtask_id):
    subtask = get_object_or_404(SubTask, id=subtask_id, todo__user=request.user)
    subtask.done = not subtask.done
    subtask.save()
    return redirect("todo_list")

@login_required
def subtask_delete(request, subtask_id):
    subtask = get_object_or_404(SubTask, id=subtask_id, todo__user=request.user)
    subtask.delete()
    return redirect("todo_list")


# ----------------------------------------------------
#   MODULE DE CLOTURE
# ----------------------------------------------------

@login_required
def cloture_annees(request):
    annees = ClotureAnnee.objects.all().order_by('-annee')
    return render(request, "cloture/annees.html", {"annees": annees})


@login_required
def cloture_annee_create(request):
    if request.method == "POST":
        saisie = request.POST.get("annee")

        try:
            new_year = int(saisie)
        except:
            return redirect("cloture_annees")

        # Créer ou récupérer l'année
        annee, created = ClotureAnnee.objects.get_or_create(annee=new_year)

        # Si l'année vient d'être créée → créer les fiches clients
        if created:
            from .models import Client  # ✔️ Import correct

            clients = Client.objects.all()

            for client in clients:
                ClotureClient.objects.get_or_create(
                    annee=annee,
                    client=client
                )

        return redirect("cloture_annees")

@login_required
def cloture_clients(request, annee_id):
    annee = ClotureAnnee.objects.get(id=annee_id)
    clotures = ClotureClient.objects.filter(annee=annee).select_related("client")
    annees = ClotureAnnee.objects.all().order_by('-annee')

    return render(request, "cloture/clients.html", {
        "annee": annee,
        "clotures": clotures,
        "annees": annees,
    })


@login_required
def cloture_client_detail(request, cloture_id):
    cloture = get_object_or_404(ClotureClient, id=cloture_id)

    if request.method == "POST":
        form = ClotureClientForm(request.POST, instance=cloture)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.utilisateur_maj = request.user
            instance.save()
            return redirect("cloture_client_detail", cloture_id=cloture.id)
    else:
        form = ClotureClientForm(instance=cloture)

    return render(request, "cloture/detail.html", {
        "cloture": cloture,
        "form": form,
    })

