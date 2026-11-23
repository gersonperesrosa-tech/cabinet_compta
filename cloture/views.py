from django.contrib.auth.decorators import login_required
import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from dossiers.models import Client
from .models import (
    ModuleRevision,
    ModulePlaquettesLiasse,
    ClotureStatus,
    ClotureAnnee,
    ModuleCA12,
    ModuleISCI,
    ModuleDeclarations,
    ModuleMission,
    ModuleJuridique,
    ClotureExperimentaleLigne,
    ClotureExperimentaleCellule,
)


EXPERIMENTAL_COLUMNS = (
    ("pre_revision", "Pré-révision"),
    ("relance_pieces", "Relance de pièces"),
    ("releve_bancaire", "Relevé bancaire"),
    ("revision_ad", "Révision AD"),
    ("plaquette", "Plaquette"),
    ("liasse", "Liasse"),
    ("ca12", "CA12"),
    ("is_ci", "IS/CI"),
    ("va1330", "VA1330"),
    ("def1329", "1329DEF"),
    ("decloyer", "DECLOYER"),
    ("das2", "DAS2"),
    ("dri", "DRI"),
    ("lab_maintien", "LAB/Laintien"),
    ("dossier_travail", "Dossier travail"),
    ("attestation", "Attestation"),
    ("cr_mission", "CR Mission"),
)
EXPERIMENTAL_COLUMN_KEYS = {key for key, _label in EXPERIMENTAL_COLUMNS}
EXPERIMENTAL_COLOR_ORDER = ("none", "gray", "yellow", "orange", "light_green", "dark_green", "red")
EXPERIMENTAL_COLORS = set(EXPERIMENTAL_COLOR_ORDER)


def _experimental_status(colors):
    """Applique les règles de statut dans l'ordre demandé."""
    if all(color == "none" for color in colors):
        return ClotureExperimentaleLigne.STATUT_NON_COMMENCE
    if all(color in {"gray", "dark_green"} for color in colors):
        return ClotureExperimentaleLigne.STATUT_TERMINE
    return ClotureExperimentaleLigne.STATUT_EN_COURS


def _experimental_status_label(status):
    return dict(ClotureExperimentaleLigne.STATUT_CHOICES)[status]


def _serialize_experimental_row(row):
    cells = {cell.colonne: cell for cell in row.cellules.all()}
    colors = {key: cells.get(key).couleur if key in cells else "none" for key in EXPERIMENTAL_COLUMN_KEYS}
    return {
        "id": row.client_id,
        "client_id": row.client_id,
        "numero_client": row.client.numero,
        "client": row.client.nom,
        "version": row.version,
        "colors": colors,
        "statut_general": _experimental_status_label(row.statut_general),
        "statut_code": row.statut_general,
        **{key: cells.get(key).texte if key in cells else "" for key in EXPERIMENTAL_COLUMN_KEYS},
    }


# ----------------------------------------------------
#   Accueil des années
# ----------------------------------------------------

@login_required
def cloture_home(request):
    annees = ClotureAnnee.objects.all().order_by("-annee")
    return render(request, "cloture/home.html", {"annees": annees})


# ----------------------------------------------------
#   Création d'une année
# ----------------------------------------------------

@login_required
def cloture_create(request):
    # Récupérer les années existantes pour les afficher en bas du template
    annees = ClotureAnnee.objects.all().order_by("-annee")

    if request.method == "POST":
        annee = request.POST.get("annee")
        if annee:
            cloture = ClotureAnnee.objects.create(annee=annee)
            return redirect("cloture_detail", cloture_id=cloture.id)

    return render(request, "cloture/create.html", {
        "annees": annees,
    })


# ----------------------------------------------------
#   Détail d'une année
# ----------------------------------------------------

@login_required
def cloture_detail(request, cloture_id):
    cloture = get_object_or_404(ClotureAnnee, id=cloture_id)

    clients_data = []
    for client in cloture.clients.order_by("nom"):
        clients_data.append({
            "client": client,
            "revision": ModuleRevision.objects.filter(cloture=cloture, client=client).first(),
            "plaquettes_liasse": ModulePlaquettesLiasse.objects.filter(cloture=cloture, client=client).first(),
        })

    return render(request, "cloture/detail.html", {
        "cloture": cloture,
        "clients_data": clients_data,
    })


# ----------------------------------------------------
#   Ajout de clients + création automatique des modules
# ----------------------------------------------------

@login_required
def cloture_add_clients(request, cloture_id):
    cloture = get_object_or_404(ClotureAnnee, id=cloture_id)
    clients = Client.objects.filter(archive=False).order_by("nom")

    if request.method == "POST":
        selected_ids = request.POST.getlist("clients")

        for client_id in selected_ids:
            client = Client.objects.get(id=client_id)

            # Ajout du client à l'année
            cloture.clients.add(client)

            # Création automatique des sous-modules
            ModuleRevision.objects.get_or_create(
                cloture=cloture,
                client=client,
                defaults={"statut_general": "non_commence"}
            )

            ModulePlaquettesLiasse.objects.get_or_create(
                cloture=cloture,
                client=client,
                defaults={"statut_general": "non_commence"}
            )

            ModuleCA12.objects.get_or_create(
                cloture=cloture,
                client=client,
                defaults={"statut_general": "non_commence"}
            )

            ModuleISCI.objects.get_or_create(
                cloture=cloture,
                client=client,
                defaults={"statut_general": "non_commence"}
            )

            ModuleDeclarations.objects.get_or_create(
                cloture=cloture,
                client=client,
                defaults={"statut_general": "non_commence"}
            )

            ModuleMission.objects.get_or_create(
                cloture=cloture,
                client=client,
                defaults={"statut_general": "non_commence"}
            )

            ModuleJuridique.objects.get_or_create(
                cloture=cloture,
                client=client,
                defaults={"statut_general": "non_commence"}
            )


        return redirect("cloture_detail", cloture_id=cloture.id)

    return render(request, "cloture/add_clients.html", {
        "cloture": cloture,
        "clients": clients,
    })


# ----------------------------------------------------
#   Suppression d'un client + modules associés
# ----------------------------------------------------

@login_required
def cloture_remove_client(request, cloture_id, client_id):
    cloture = get_object_or_404(ClotureAnnee, id=cloture_id)
    client = get_object_or_404(Client, id=client_id)

    cloture.clients.remove(client)

    ModuleRevision.objects.filter(cloture=cloture, client=client).delete()
    ModulePlaquettesLiasse.objects.filter(cloture=cloture, client=client).delete()
    ModuleCA12.objects.filter(cloture=cloture, client=client).delete()
    ModuleISCI.objects.filter(cloture=cloture, client=client).delete()
    ModuleDeclarations.objects.filter(cloture=cloture, client=client).delete()
    ModuleMission.objects.filter(cloture=cloture, client=client).delete()
    ModuleJuridique.objects.filter(cloture=cloture, client=client).delete()

    return redirect("cloture_detail", cloture_id=cloture.id)


# ----------------------------------------------------
#   Module Révision
# ----------------------------------------------------

@login_required
def revision_detail(request, module_id):
    module = get_object_or_404(ModuleRevision, id=module_id)

    if request.method == "POST":
        module.pre_revision = request.POST.get("pre_revision") or ""
        module.statut_pre_revision = request.POST.get("statut_pre_revision") or ""

        module.relance_pieces = request.POST.get("relance_pieces") or ""
        module.statut_relance_pieces = request.POST.get("statut_relance_pieces") or ""

        module.releve_bancaire = request.POST.get("releve_bancaire") or ""
        module.statut_releve_bancaire = request.POST.get("statut_releve_bancaire") or ""

        module.revision_ad = request.POST.get("revision_ad") or ""
        module.statut_revision_ad = request.POST.get("statut_revision_ad") or ""

        # -------------------------------
        # NOUVEAUX CHAMPS PLAQUETTE/LIASSE
        # -------------------------------
        module.plaquette_envoi_client = request.POST.get("plaquette_envoi_client") or ""
        module.statut_plaquette_envoi_client = request.POST.get("statut_plaquette_envoi_client") or ""

        module.liasse_envoi_client = request.POST.get("liasse_envoi_client") or ""
        module.statut_liasse_envoi_client = request.POST.get("statut_liasse_envoi_client") or ""

        # -------------------------------
        # STATUT GÉNÉRAL
        # -------------------------------
        module.statut_general = request.POST.get("statut_general") or ""

        module.save()

        annee = module.cloture.annee
        return redirect(f"/cloture/revisions/?annee={annee}")

    return render(request, "cloture/revision_detail.html", {
        "module": module,
        "statuts": ClotureStatus.choices,
    })

@login_required
def gestion_revisions(request):
    selected_year = request.GET.get("annee")
    annees = ClotureAnnee.objects.order_by("-annee")

    if selected_year:
        revisions = ModuleRevision.objects.select_related("client", "cloture") \
            .filter(cloture__annee=selected_year) \
            .order_by("client__nom")
    else:
        revisions = ModuleRevision.objects.select_related("client", "cloture") \
            .order_by("-cloture__annee", "client__nom")

    return render(request, "cloture/gestion_revisions.html", {
        "revisions": revisions,
        "annees": annees,
        "selected_year": selected_year,
        "statuts": ClotureStatus.choices,
        "filter_columns": [(2, "Pré-révision"), (3, "Relance pièces"), (4, "Relevé bancaire"), (5, "Révision AD"), (6, "Plaquette"), (7, "Liasse"), (8, "Statut général")],
    })


# ----------------------------------------------------
#   Module Plaquettes & Liasse
# ----------------------------------------------------

@login_required
def plaquettes_liasse_detail(request, module_id):
    module = get_object_or_404(ModulePlaquettesLiasse, id=module_id)

    if request.method == "POST":
        fields = [
            "plaquette_envoi_client", "statut_plaquette_envoi_client",
            "plaquette_retour_client", "statut_plaquette_retour_client",
            "liasse_envoi_client", "statut_liasse_envoi_client",
            "liasse_retour_client", "statut_liasse_retour_client",
            "ca_152500",
            "statut_general"
        ]

        for f in fields:
            setattr(module, f, request.POST.get(f))

        module.save()

        annee = module.cloture.annee
        return redirect(f"/cloture/plaquettes-liasse/?annee={annee}")

    return render(request, "cloture/plaquettes_liasse_detail.html", {
        "module": module,
        "statuts": ClotureStatus.choices,
    })

@login_required
def gestion_plaquettes_liasse(request):
    selected_year = request.GET.get("annee")
    annees = ClotureAnnee.objects.order_by("-annee")

    if selected_year:
        modules = ModulePlaquettesLiasse.objects.select_related("client", "cloture") \
            .filter(cloture__annee=selected_year) \
            .order_by("client__nom")
    else:
        modules = ModulePlaquettesLiasse.objects.select_related("client", "cloture") \
            .order_by("-cloture__annee", "client__nom")

    return render(request, "cloture/gestion_plaquettes_liasse.html", {
        "modules": modules,
        "annees": annees,
        "selected_year": selected_year,
    })

# ----------------------------------------------------
#   Module Cloture CA12
# ----------------------------------------------------

@login_required
def ca12_detail(request, module_id):
    module = get_object_or_404(ModuleCA12, id=module_id)

    if request.method == "POST":
        module.ca12_faite = request.POST.get("ca12_faite")
        module.statut_ca12_faite = request.POST.get("statut_ca12_faite")

        module.ca12_envoyee = request.POST.get("ca12_envoyee")
        module.statut_ca12_envoyee = request.POST.get("statut_ca12_envoyee")

        module.statut_general = request.POST.get("statut_general")

        module.save()

        annee = module.cloture.annee
        return redirect(f"/cloture/ca12/?annee={annee}")

    return render(request, "cloture/ca12_detail.html", {
        "module": module,
        "statuts": ClotureStatus.choices,
    })

@login_required
def gestion_ca12(request):
    selected_year = request.GET.get("annee")
    annees = ClotureAnnee.objects.order_by("-annee")

    if selected_year:
        modules = ModuleCA12.objects.select_related("client", "cloture") \
            .filter(cloture__annee=selected_year) \
            .order_by("client__nom")
    else:
        modules = ModuleCA12.objects.select_related("client", "cloture") \
            .order_by("-cloture__annee", "client__nom")

    return render(request, "cloture/gestion_ca12.html", {
        "modules": modules,
        "annees": annees,
        "selected_year": selected_year,
    })


# ----------------------------------------------------
#   Module IS/CI
# ----------------------------------------------------

@login_required
def isci_detail(request, module_id):
    module = get_object_or_404(ModuleISCI, id=module_id)

    if request.method == "POST":
        module.is_fait = request.POST.get("is_fait")
        module.statut_is_fait = request.POST.get("statut_is_fait")

        module.is_envoi = request.POST.get("is_envoi")
        module.statut_is_envoi = request.POST.get("statut_is_envoi")

        module.statut_general = request.POST.get("statut_general")

        module.save()

        annee = module.cloture.annee
        return redirect(f"/cloture/isci/?annee={annee}")

    return render(request, "cloture/isci_detail.html", {
        "module": module,
        "statuts": ClotureStatus.choices,
    })


@login_required
def gestion_isci(request):
    selected_year = request.GET.get("annee")
    annees = ClotureAnnee.objects.order_by("-annee")

    if selected_year:
        modules = ModuleISCI.objects.select_related("client", "cloture") \
            .filter(cloture__annee=selected_year) \
            .order_by("client__nom")
    else:
        modules = ModuleISCI.objects.select_related("client", "cloture") \
            .order_by("-cloture__annee", "client__nom")

    return render(request, "cloture/gestion_isci.html", {
        "modules": modules,
        "annees": annees,
        "selected_year": selected_year,
    })

# ----------------------------------------------------
#   Module Cloture déclarations
# ----------------------------------------------------

@login_required
def gestion_declarations(request):
    selected_year = request.GET.get("annee")
    annees = ClotureAnnee.objects.order_by("-annee")

    if selected_year:
        modules = ModuleDeclarations.objects.select_related("client", "cloture") \
            .filter(cloture__annee=selected_year) \
            .order_by("client__nom")
    else:
        modules = ModuleDeclarations.objects.select_related("client", "cloture") \
            .order_by("-cloture__annee", "client__nom")

    return render(request, "cloture/gestion_declarations.html", {
        "modules": modules,
        "annees": annees,
        "selected_year": selected_year,
        "statuts": ClotureStatus.choices,
        "filter_columns": [(2, "CA12"), (3, "IS / CI"), (4, "VA1330"), (5, "1329DEF"), (6, "DECLOYER"), (7, "DAS2"), (8, "DRI"), (9, "Statut général")],
    })


@login_required
def declarations_detail(request, module_id):
    module = get_object_or_404(ModuleDeclarations, id=module_id)

    if request.method == "POST":
        fields = [
            "ca12_decl_cloture", "statut_ca12_decl_cloture",
            "is_decl_cloture", "statut_is_decl_cloture",
            "va1330_fait", "statut_va1330_fait",
            "va1330_envoi", "statut_va1330_envoi",
            "cvae1329_fait", "statut_cvae1329_fait",
            "cvae1329_envoi", "statut_cvae1329_envoi",
            "decloyer_fait", "statut_decloyer_fait",
            "das2_fait", "statut_das2_fait",
            "dri_fait", "statut_dri_fait",
            "dri_envoi", "statut_dri_envoi",
            "statut_general"
        ]

        for f in fields:
            setattr(module, f, request.POST.get(f))

        module.save()

        annee = module.cloture.annee
        return redirect(f"/cloture/declarations/?annee={annee}")

    return render(request, "cloture/declarations_detail.html", {
        "module": module,
        "statuts": ClotureStatus.choices,
    })

# ----------------------------------------------------
#   Module Cloture Missions
# ----------------------------------------------------

@login_required
def gestion_mission(request):
    selected_year = request.GET.get("annee")
    annees = ClotureAnnee.objects.order_by("-annee")

    if selected_year:
        modules = ModuleMission.objects.select_related("client", "cloture") \
            .filter(cloture__annee=selected_year) \
            .order_by("client__nom")
    else:
        modules = ModuleMission.objects.select_related("client", "cloture") \
            .order_by("-cloture__annee", "client__nom")

    return render(request, "cloture/gestion_mission.html", {
        "modules": modules,
        "annees": annees,
        "selected_year": selected_year,
        "statuts": ClotureStatus.choices,
        "filter_columns": [(2, "LAB/Maintien"), (3, "Dossier travail"), (4, "Attestation"), (5, "CR Mission"), (6, "Statut général")],
    })


@login_required
def mission_detail(request, module_id):
    module = get_object_or_404(ModuleMission, id=module_id)

    if request.method == "POST":
        fields = [
            "lab_maintien", "statut_lab_maintien",
            "dossier_travail", "statut_dossier_travail",
            "attestation", "statut_attestation",
            "cr_mission", "statut_cr_mission",
            "statut_general"
        ]

        for f in fields:
            setattr(module, f, request.POST.get(f))

        module.save()

        annee = module.cloture.annee
        return redirect(f"/cloture/mission/?annee={annee}")

    return render(request, "cloture/mission_detail.html", {
        "module": module,
        "statuts": ClotureStatus.choices,
    })

# ----------------------------------------------------
#   Module Cloture Juridique
# ----------------------------------------------------

@login_required
def gestion_juridique(request):
    selected_year = request.GET.get("annee")
    annees = ClotureAnnee.objects.order_by("-annee")

    if selected_year:
        modules = ModuleJuridique.objects.select_related("client", "cloture") \
            .filter(cloture__annee=selected_year) \
            .order_by("client__nom")
    else:
        modules = ModuleJuridique.objects.select_related("client", "cloture") \
            .order_by("-cloture__annee", "client__nom")

    return render(request, "cloture/gestion_juridique.html", {
        "modules": modules,
        "annees": annees,
        "selected_year": selected_year,
        "statuts": ClotureStatus.choices,
        "filter_columns": [(2, "Juridique fait"), (3, "Envoi client"), (4, "Retour client"), (5, "Envoi greffe"), (6, "Validation greffe"), (7, "Statut général")],
    })


@login_required
def juridique_detail(request, module_id):
    module = get_object_or_404(ModuleJuridique, id=module_id)

    if request.method == "POST":
        fields = [
            "juridique_fait", "statut_juridique_fait",
            "juridique_envoi_client", "statut_juridique_envoi_client",
            "retour_client", "statut_retour_client",
            "envoi_greffe", "statut_envoi_greffe",
            "validation_greffe", "statut_validation_greffe",
            "statut_general"
        ]

        for f in fields:
            setattr(module, f, request.POST.get(f))

        module.save()

        annee = module.cloture.annee
        return redirect(f"/cloture/juridique/?annee={annee}")

    return render(request, "cloture/juridique_detail.html", {
        "module": module,
        "statuts": ClotureStatus.choices,
    })

# ----------------------------------------------------
#   Page de gestion globale
# ----------------------------------------------------

@login_required
def gestion_globale_cloture(request):
    selected_year = request.GET.get("annee")
    annees = ClotureAnnee.objects.order_by("-annee")

    if selected_year:
        cloture = ClotureAnnee.objects.filter(annee=selected_year).first()
        clients = cloture.clients.order_by("nom") if cloture else []
    else:
        clients = Client.objects.none()

    data = []
    for client in clients:
        row = {"client": client}

        # Récupération des modules
        row["revision"] = ModuleRevision.objects.filter(client=client, cloture__annee=selected_year).first()
        row["declarations"] = ModuleDeclarations.objects.filter(client=client, cloture__annee=selected_year).first()
        row["mission"] = ModuleMission.objects.filter(client=client, cloture__annee=selected_year).first()
        row["juridique"] = ModuleJuridique.objects.filter(client=client, cloture__annee=selected_year).first()

        # Liste des statuts (on garde NA dans la liste cette fois)
        statuts = [
        m.statut_general
            for m in [
                row["revision"],
                row["declarations"], row["mission"], row["juridique"]
            ]
            if m is not None
        ]

        # Si aucun module n'existe
        if not statuts:
            row["statut_global"] = "non_commence"

        # Si tous les statuts sont dans {na, termine, envoye}
        elif all(s in ["na", "termine", "envoye"] for s in statuts):
            row["statut_global"] = "termine"

        # Si tous = non_commence
        elif all(s == "non_commence" for s in statuts):
            row["statut_global"] = "non_commence"

        # Sinon = en cours
        else:
            row["statut_global"] = "en_cours"

        data.append(row)

    return render(request, "cloture/gestion_globale_cloture.html", {
        "annees": annees,
        "selected_year": selected_year,
        "data": data,
        "statuts": ClotureStatus.choices,
        "filter_columns": [(2, "Révisions, Plaquette et Liasse"), (3, "Déclarations"), (4, "Mission"), (5, "Juridique"), (6, "Statut général")],
    })


# ----------------------------------------------------
#   Tableau expérimental (stockage totalement séparé)
# ----------------------------------------------------

@login_required
@ensure_csrf_cookie
def tableau_experimental_cloture(request):
    annees = ClotureAnnee.objects.order_by("-annee")
    selected_year = request.GET.get("annee")
    cloture = None
    if selected_year:
        cloture = ClotureAnnee.objects.filter(annee=selected_year).first()
    elif annees.exists():
        cloture = annees.first()
        selected_year = str(cloture.annee)

    rows = []
    if cloture:
        # Seuls les clients effectivement liés à cette clôture figurent ici.
        for client in cloture.clients.order_by("nom", "id"):
            row, _created = ClotureExperimentaleLigne.objects.get_or_create(
                cloture=cloture,
                client=client,
            )
            existing_columns = set(row.cellules.values_list("colonne", flat=True))
            missing_cells = [
                ClotureExperimentaleCellule(ligne=row, colonne=key)
                for key in EXPERIMENTAL_COLUMN_KEYS - existing_columns
            ]
            if missing_cells:
                ClotureExperimentaleCellule.objects.bulk_create(missing_cells)
        rows = list(
            ClotureExperimentaleLigne.objects.filter(cloture=cloture)
            .select_related("client")
            .prefetch_related("cellules")
            .order_by("client__nom", "client__id")
        )

    return render(request, "cloture/tableau_experimental.html", {
        "annees": annees,
        "selected_year": selected_year,
        "selected_cloture_id": cloture.id if cloture else None,
        "table_rows": [_serialize_experimental_row(row) for row in rows],
        "experimental_columns": EXPERIMENTAL_COLUMNS,
        "experimental_color_order": EXPERIMENTAL_COLOR_ORDER,
    })


@login_required
@require_POST
def sauvegarder_cellule_experimentale(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "Données de sauvegarde invalides."}, status=400)

    client_id = payload.get("client_id")
    column = payload.get("column")
    text = payload.get("text")
    color = payload.get("color")
    expected_version = payload.get("version")
    try:
        cloture_id = int(payload.get("cloture_id"))
        client_id = int(client_id)
        expected_version = int(expected_version)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Identifiant ou version invalide."}, status=400)

    if column not in EXPERIMENTAL_COLUMN_KEYS or color not in EXPERIMENTAL_COLORS:
        return JsonResponse({"error": "Colonne ou couleur non autorisée."}, status=400)
    if not isinstance(text, str):
        return JsonResponse({"error": "Le texte doit être une chaîne."}, status=400)
    if len(text) > 10000:
        return JsonResponse({"error": "Le texte est trop long."}, status=400)

    with transaction.atomic():
        cloture = get_object_or_404(ClotureAnnee, pk=cloture_id)
        # Cette vérification interdit toute écriture sur un client hors du
        # périmètre réel de l'année de clôture.
        client = get_object_or_404(cloture.clients, pk=client_id)
        row, _created = ClotureExperimentaleLigne.objects.select_for_update().get_or_create(
            cloture=cloture,
            client=client,
        )
        if row.version != expected_version:
            row = ClotureExperimentaleLigne.objects.select_related("client").prefetch_related("cellules").get(pk=row.pk)
            return JsonResponse({
                "error": "Cette ligne a été modifiée dans un autre onglet. Actualisez-la avant de continuer.",
                "row": _serialize_experimental_row(row),
            }, status=409)

        cell, _created = ClotureExperimentaleCellule.objects.get_or_create(
            ligne=row,
            colonne=column,
            defaults={"texte": text, "couleur": color},
        )
        if not _created:
            cell.texte = text
            cell.couleur = color
            cell.save(update_fields=("texte", "couleur", "updated_at"))

        colors = dict(row.cellules.values_list("colonne", "couleur"))
        colors[column] = color
        row.statut_general = _experimental_status([
            colors.get(key, "none") for key in EXPERIMENTAL_COLUMN_KEYS
        ])
        row.version += 1
        row.save(update_fields=("statut_general", "version", "updated_at"))

    return JsonResponse({
        "version": row.version,
        "statut_code": row.statut_general,
        "statut_general": _experimental_status_label(row.statut_general),
    })
