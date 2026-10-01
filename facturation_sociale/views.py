from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    NouvellePrestationForm,
    PrestataireSocialForm,
    TarifPrestataireForm,
    TypePrestationForm,
)
from .models import (
    PrestataireSocial,
    PrestationSociale,
    TarifPrestataire,
    TypePrestation,
)


def gestion(request):
    from calendar import monthrange
    from datetime import date
    from decimal import Decimal

    # ---------------------------------------------------------
    # PÉRIODE
    # ---------------------------------------------------------

    today = date.today()

    try:
        mois = int(request.GET.get("mois", today.month))
        annee = int(request.GET.get("annee", today.year))
    except (TypeError, ValueError):
        mois = today.month
        annee = today.year

    if mois < 1 or mois > 12:
        mois = today.month

    if annee < 2000 or annee > 2100:
        annee = today.year


    mois_noms = [
        "",
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ]


    # Mois précédent
    if mois == 1:
        mois_precedent = 12
        annee_precedente = annee - 1
    else:
        mois_precedent = mois - 1
        annee_precedente = annee


    # Mois suivant
    if mois == 12:
        mois_suivant = 1
        annee_suivante = annee + 1
    else:
        mois_suivant = mois + 1
        annee_suivante = annee


    # ---------------------------------------------------------
    # PRESTATIONS DE LA PÉRIODE
    # ---------------------------------------------------------

    prestations = list(
        PrestationSociale.objects
        .filter(
            mois=mois,
            annee=annee,
        )
        .select_related(
            "client",
            "prestation",
            "prestataire",
        )
        .order_by(
            "client__nom",
            "prestation__nom",
            "prestataire__nom",
        )
    )


    # ---------------------------------------------------------
    # KPI
    # ---------------------------------------------------------

    total_facture = sum(
        (
            prestation.montant_facture
            for prestation in prestations
        ),
        Decimal("0.00"),
    )

    total_cout = sum(
        (
            prestation.cout_total
            for prestation in prestations
        ),
        Decimal("0.00"),
    )

    total_marge = sum(
        (
            prestation.marge
            for prestation in prestations
        ),
        Decimal("0.00"),
    )

    clients_ids = {
        prestation.client_id
        for prestation in prestations
    }

    nombre_clients = len(clients_ids)


    # ---------------------------------------------------------
    # SYNTHÈSE PAR CLIENT
    # ---------------------------------------------------------

    clients_dict = {}

    for ligne in prestations:

        client_id = ligne.client_id

        if client_id not in clients_dict:
            clients_dict[client_id] = {
                "client": ligne.client,
                "nombre_lignes": 0,
                "quantite": Decimal("0.00"),
                "facture": Decimal("0.00"),
                "cout": Decimal("0.00"),
                "marge": Decimal("0.00"),
                "prestations": [],
            }

        client_data = clients_dict[client_id]

        client_data["nombre_lignes"] += 1
        client_data["quantite"] += ligne.quantite
        client_data["facture"] += ligne.montant_facture
        client_data["cout"] += ligne.cout_total
        client_data["marge"] += ligne.marge

        client_data["prestations"].append(ligne)


    synthese_clients = list(
        clients_dict.values()
    )


    # ---------------------------------------------------------
    # SYNTHÈSE PAR TYPE DE PRESTATION
    # ---------------------------------------------------------

    prestations_dict = {}

    for ligne in prestations:

        prestation_id = ligne.prestation_id

        if prestation_id not in prestations_dict:
            prestations_dict[prestation_id] = {
                "prestation": ligne.prestation,
                "nombre_lignes": 0,
                "quantite": Decimal("0.00"),
                "facture": Decimal("0.00"),
                "cout": Decimal("0.00"),
                "marge": Decimal("0.00"),
            }

        data = prestations_dict[prestation_id]

        data["nombre_lignes"] += 1
        data["quantite"] += ligne.quantite
        data["facture"] += ligne.montant_facture
        data["cout"] += ligne.cout_total
        data["marge"] += ligne.marge


    synthese_prestations = sorted(
        prestations_dict.values(),
        key=lambda item: item["prestation"].nom.lower(),
    )


    # ---------------------------------------------------------
    # CONTEXTE
    # ---------------------------------------------------------

    context = {
        "mois": mois,
        "annee": annee,
        "mois_nom": mois_noms[mois],

        "mois_precedent": mois_precedent,
        "annee_precedente": annee_precedente,

        "mois_suivant": mois_suivant,
        "annee_suivante": annee_suivante,

        "total_facture": total_facture,
        "total_cout": total_cout,
        "total_marge": total_marge,
        "nombre_clients": nombre_clients,

        "prestations": prestations,
        "synthese_clients": synthese_clients,
        "synthese_prestations": synthese_prestations,
    }

    return render(
        request,
        "facturation_sociale/gestion.html",
        context,
    )


def modifier_prestation_sociale(request, pk):
    from django.contrib import messages
    from django.shortcuts import get_object_or_404, redirect

    ligne = get_object_or_404(
        PrestationSociale.objects.select_related(
            "client",
            "prestation",
            "prestataire",
        ),
        pk=pk,
    )

    if request.method == "POST":
        form = NouvellePrestationForm(request.POST)

        if form.is_valid():

            prestation = form.cleaned_data["prestation"]
            tarif_prestataire = form.cleaned_data["tarif_prestataire_obj"]

            tarif_standard = prestation.tarif_client_standard

            mode_tarification = form.cleaned_data["mode_tarification"]

            if mode_tarification == "personnalise":
                tarif_applique = form.cleaned_data["tarif_client_personnalise"]
                tarif_personnalise = True
                motif = form.cleaned_data.get("motif_tarif_personnalise", "")
            else:
                tarif_applique = tarif_standard
                tarif_personnalise = False
                motif = ""

            ligne.client = form.cleaned_data["client"]
            ligne.prestation = prestation
            ligne.prestataire = form.cleaned_data["prestataire"]

            ligne.mois = form.cleaned_data["mois"]
            ligne.annee = form.cleaned_data["annee"]

            ligne.detail = form.cleaned_data.get("detail", "")
            ligne.quantite = form.cleaned_data["quantite"]

            # Nouveaux snapshots correspondant à la modification volontaire
            ligne.tarif_client_standard_snapshot = tarif_standard
            ligne.tarif_client_applique = tarif_applique
            ligne.tarif_personnalise = tarif_personnalise
            ligne.motif_tarif_personnalise = motif

            cout_prestataire_standard = tarif_prestataire.cout_unitaire

            if form.cleaned_data["mode_cout_prestataire"] == "personnalise":
                cout_prestataire_applique = form.cleaned_data[
                    "cout_prestataire_personnalise"
                ]
                cout_prestataire_personnalise = True
                motif_cout_prestataire = form.cleaned_data.get(
                    "motif_cout_prestataire_personnalise",
                    "",
                )
            else:
                cout_prestataire_applique = cout_prestataire_standard
                cout_prestataire_personnalise = False
                motif_cout_prestataire = ""

            ligne.cout_prestataire_standard_snapshot = (
                cout_prestataire_standard
            )
            ligne.cout_prestataire_unitaire_snapshot = (
                cout_prestataire_applique
            )
            ligne.cout_prestataire_personnalise = (
                cout_prestataire_personnalise
            )
            ligne.motif_cout_prestataire_personnalise = (
                motif_cout_prestataire
            )

            ligne.save()

            messages.success(
                request,
                "La prestation a été modifiée avec succès."
            )

            return redirect(
                f"/facturation-sociale/gestion/?mois={ligne.mois}&annee={ligne.annee}"
            )

    else:

        initial = {
            "mois": ligne.mois,
            "annee": ligne.annee,
            "client": ligne.client_id,
            "prestation": ligne.prestation_id,
            "prestataire": ligne.prestataire_id,
            "detail": ligne.detail,
            "quantite": ligne.quantite,

            "mode_tarification": (
                "personnalise"
                if ligne.tarif_personnalise
                else "standard"
            ),

            "tarif_client_personnalise": (
                ligne.tarif_client_applique
                if ligne.tarif_personnalise
                else None
            ),

            "motif_tarif_personnalise": (
                ligne.motif_tarif_personnalise
            ),

            "mode_cout_prestataire": (
                "personnalise"
                if ligne.cout_prestataire_personnalise
                else "standard"
            ),

            "cout_prestataire_personnalise": (
                ligne.cout_prestataire_unitaire_snapshot
                if ligne.cout_prestataire_personnalise
                else None
            ),

            "motif_cout_prestataire_personnalise": (
                ligne.motif_cout_prestataire_personnalise
            ),
        }

        form = NouvellePrestationForm(initial=initial)

    clients_queryset = form.fields["client"].queryset

    context = {
        "form": form,

        "mode_modification": True,
        "ligne_modifiee": ligne,

        "tarifs_prestataires": list(
            TarifPrestataire.objects
            .filter(actif=True)
            .values(
                "prestation_id",
                "prestataire_id",
                "cout_unitaire",
            )
        ),

        "prestations_data": list(
            TypePrestation.objects
            .filter(actif=True)
            .values(
                "id",
                "tarif_client_standard",
            )
        ),

        "clients_paie_ids": list(
            clients_queryset
            .filter(module_paie=True)
            .values_list("id", flat=True)
        ),
    }

    return render(
        request,
        "facturation_sociale/nouvelle_prestation.html",
        context,
    )


def supprimer_prestation_sociale(request, pk):
    from django.contrib import messages
    from django.http import HttpResponseNotAllowed
    from django.shortcuts import get_object_or_404, redirect

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    ligne = get_object_or_404(
        PrestationSociale,
        pk=pk,
    )

    mois = ligne.mois
    annee = ligne.annee

    ligne.delete()

    messages.success(
        request,
        "La prestation a été supprimée."
    )

    return redirect(
        f"/facturation-sociale/gestion/?mois={mois}&annee={annee}"
    )

def nouvelle_prestation(request):

    if request.method == "POST":
        form = NouvellePrestationForm(request.POST)

        if form.is_valid():

            prestation = form.cleaned_data["prestation"]
            tarif_prestataire = (
                form.cleaned_data["tarif_prestataire_obj"]
            )

            tarif_standard = (
                prestation.tarif_client_standard
            )

            if (
                form.cleaned_data["mode_tarification"]
                == "personnalise"
            ):
                tarif_applique = (
                    form.cleaned_data[
                        "tarif_client_personnalise"
                    ]
                )
                tarif_personnalise = True

            else:
                tarif_applique = tarif_standard
                tarif_personnalise = False
            # Coût prestataire :
            # le tarif configuré reste la référence standard.
            cout_prestataire_standard = (
                tarif_prestataire.cout_unitaire
            )

            if (
                form.cleaned_data["mode_cout_prestataire"]
                == "personnalise"
            ):
                cout_prestataire_applique = (
                    form.cleaned_data[
                        "cout_prestataire_personnalise"
                    ]
                )
                cout_prestataire_personnalise = True
                motif_cout_prestataire = (
                    form.cleaned_data.get(
                        "motif_cout_prestataire_personnalise",
                        "",
                    )
                )
            else:
                cout_prestataire_applique = (
                    cout_prestataire_standard
                )
                cout_prestataire_personnalise = False
                motif_cout_prestataire = ""

            prestation_sociale = PrestationSociale(
                client=form.cleaned_data["client"],
                prestation=prestation,
                prestataire=form.cleaned_data["prestataire"],
                mois=form.cleaned_data["mois"],
                annee=form.cleaned_data["annee"],
                detail=form.cleaned_data["detail"],
                quantite=form.cleaned_data["quantite"],

                tarif_client_standard_snapshot=(
                    tarif_standard
                ),

                tarif_client_applique=(
                    tarif_applique
                ),

                tarif_personnalise=(
                    tarif_personnalise
                ),

                motif_tarif_personnalise=(
                    form.cleaned_data[
                        "motif_tarif_personnalise"
                    ]
                    if tarif_personnalise
                    else ""
                ),

                cout_prestataire_standard_snapshot=(
                    cout_prestataire_standard
                ),

                cout_prestataire_unitaire_snapshot=(
                    cout_prestataire_applique
                ),

                cout_prestataire_personnalise=(
                    cout_prestataire_personnalise
                ),

                motif_cout_prestataire_personnalise=(
                    motif_cout_prestataire
                ),
            )

            prestation_sociale.save()

            messages.success(
                request,
                "La prestation a été enregistrée avec succès.",
            )

            return redirect(
                "facturation_sociale:nouvelle_prestation"
            )

    else:
        form = NouvellePrestationForm()

    # Données nécessaires au JavaScript.
    tarifs_prestataires = list(
        TarifPrestataire.objects
        .filter(
            actif=True,
            prestation__actif=True,
            prestataire__actif=True,
        )
        .values(
            "prestation_id",
            "prestataire_id",
            "cout_unitaire",
        )
    )

    prestations_data = list(
        TypePrestation.objects
        .filter(actif=True)
        .values(
            "id",
            "tarif_client_standard",
        )
    )

    clients_paie_ids = list(
        form.fields["client"].queryset
        .filter(module_paie=True)
        .values_list("id", flat=True)
    )

    context = {
        "form": form,
        "tarifs_prestataires": tarifs_prestataires,
        "prestations_data": prestations_data,
        "clients_paie_ids": clients_paie_ids,
    }

    return render(
        request,
        "facturation_sociale/nouvelle_prestation.html",
        context,
    )


def configurations(request):
    return render(
        request,
        "facturation_sociale/configurations.html",
    )


def prestations(request):
    prestations = TypePrestation.objects.all()

    if request.method == "POST":
        form = TypePrestationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "La prestation a été ajoutée avec succès.",
            )

            return redirect(
                "facturation_sociale:prestations"
            )

    else:
        form = TypePrestationForm()

    context = {
        "prestations": prestations,
        "form_prestation": form,
    }

    return render(
        request,
        "facturation_sociale/prestations.html",
        context,
    )


def modifier_prestation(request, pk):
    prestation = get_object_or_404(
        TypePrestation,
        pk=pk,
    )

    prestations = TypePrestation.objects.all()

    if request.method == "POST":
        form = TypePrestationForm(
            request.POST,
            instance=prestation,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "La prestation a été modifiée avec succès.",
            )

            return redirect(
                "facturation_sociale:prestations"
            )

    else:
        form = TypePrestationForm(
            instance=prestation
        )

    context = {
        "prestations": prestations,
        "form_prestation": form,
        "prestation_modifiee": prestation,
    }

    return render(
        request,
        "facturation_sociale/prestations.html",
        context,
    )


def prestataires(request):
    prestataires = PrestataireSocial.objects.all()

    if request.method == "POST":
        form = PrestataireSocialForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Le prestataire a été ajouté avec succès.",
            )

            return redirect(
                "facturation_sociale:prestataires"
            )

    else:
        form = PrestataireSocialForm()

    context = {
        "prestataires": prestataires,
        "form_prestataire": form,
    }

    return render(
        request,
        "facturation_sociale/prestataires.html",
        context,
    )


def modifier_prestataire(request, pk):
    prestataire = get_object_or_404(
        PrestataireSocial,
        pk=pk,
    )

    prestataires = PrestataireSocial.objects.all()

    if request.method == "POST":
        form = PrestataireSocialForm(
            request.POST,
            instance=prestataire,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Le prestataire a été modifié avec succès.",
            )

            return redirect(
                "facturation_sociale:prestataires"
            )

    else:
        form = PrestataireSocialForm(
            instance=prestataire
        )

    context = {
        "prestataires": prestataires,
        "form_prestataire": form,
        "prestataire_modifie": prestataire,
    }

    return render(
        request,
        "facturation_sociale/prestataires.html",
        context,
    )


def tarifs_prestataires(request):
    tarifs = (
        TarifPrestataire.objects
        .select_related(
            "prestation",
            "prestataire",
        )
        .all()
    )

    if request.method == "POST":
        form = TarifPrestataireForm(
            request.POST
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Le tarif prestataire a été ajouté avec succès.",
            )

            return redirect(
                "facturation_sociale:tarifs_prestataires"
            )

    else:
        form = TarifPrestataireForm()

    context = {
        "tarifs": tarifs,
        "form_tarif": form,
    }

    return render(
        request,
        "facturation_sociale/tarifs_prestataires.html",
        context,
    )


def modifier_tarif_prestataire(request, pk):
    tarif = get_object_or_404(
        TarifPrestataire.objects.select_related(
            "prestation",
            "prestataire",
        ),
        pk=pk,
    )

    tarifs = (
        TarifPrestataire.objects
        .select_related(
            "prestation",
            "prestataire",
        )
        .all()
    )

    if request.method == "POST":
        form = TarifPrestataireForm(
            request.POST,
            instance=tarif,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Le tarif prestataire a été modifié avec succès.",
            )

            return redirect(
                "facturation_sociale:tarifs_prestataires"
            )

    else:
        form = TarifPrestataireForm(
            instance=tarif
        )

    context = {
        "tarifs": tarifs,
        "form_tarif": form,
        "tarif_modifie": tarif,
    }

    return render(
        request,
        "facturation_sociale/tarifs_prestataires.html",
        context,
    )



