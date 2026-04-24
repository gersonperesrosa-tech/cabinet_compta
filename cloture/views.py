from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
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
    ModuleJuridique
)


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
    clients = Client.objects.all().order_by("nom")

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
    })


@login_required
def declarations_detail(request, module_id):
    module = get_object_or_404(ModuleDeclarations, id=module_id)

    if request.method == "POST":
        fields = [
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
        row["plaquettes"] = ModulePlaquettesLiasse.objects.filter(client=client, cloture__annee=selected_year).first()
        row["ca12"] = ModuleCA12.objects.filter(client=client, cloture__annee=selected_year).first()
        row["isci"] = ModuleISCI.objects.filter(client=client, cloture__annee=selected_year).first()
        row["declarations"] = ModuleDeclarations.objects.filter(client=client, cloture__annee=selected_year).first()
        row["mission"] = ModuleMission.objects.filter(client=client, cloture__annee=selected_year).first()
        row["juridique"] = ModuleJuridique.objects.filter(client=client, cloture__annee=selected_year).first()

        # Liste des statuts (hors N/A)
        statuts = [
            m.statut_general
            for m in [
                row["revision"], row["plaquettes"], row["ca12"],
                row["isci"], row["declarations"], row["mission"], row["juridique"]
            ]
            if m is not None and m.statut_general != "na"
        ]

        # Cas où tous les modules sont N/A
        if not statuts:
            row["statut_global"] = "non_commence"

        # Tous = non commencé
        elif all(s == "non_commence" for s in statuts):
            row["statut_global"] = "non_commence"

        # Tous = terminé
        elif all(s == "envoye" for s in statuts):
            row["statut_global"] = "envoye"

        # Sinon = en cours
        else:
            row["statut_global"] = "en_cours"

        data.append(row)

    return render(request, "cloture/gestion_globale_cloture.html", {
        "annees": annees,
        "selected_year": selected_year,
        "data": data,
    })
