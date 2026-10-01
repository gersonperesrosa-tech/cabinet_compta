from django.contrib import admin

from .models import (
    PrestationSociale,
    PrestataireSocial,
    TarifPrestataire,
    TypePrestation,
)


@admin.register(TypePrestation)
class TypePrestationAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "tarif_client_standard",
        "actif",
        "ordre",
    )
    list_editable = (
        "tarif_client_standard",
        "actif",
        "ordre",
    )
    search_fields = ("nom",)
    ordering = ("ordre", "nom")


@admin.register(PrestataireSocial)
class PrestataireSocialAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "actif",
        "ordre",
    )
    list_editable = (
        "actif",
        "ordre",
    )
    search_fields = ("nom",)
    ordering = ("ordre", "nom")


@admin.register(TarifPrestataire)
class TarifPrestataireAdmin(admin.ModelAdmin):
    list_display = (
        "prestation",
        "prestataire",
        "cout_unitaire",
        "actif",
    )
    list_filter = (
        "prestataire",
        "actif",
    )
    list_editable = (
        "cout_unitaire",
        "actif",
    )


@admin.register(PrestationSociale)
class PrestationSocialeAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "prestation",
        "prestataire",
        "mois",
        "annee",
        "quantite",
        "montant_facture",
        "cout_total",
        "marge",
        "tarif_personnalise",
    )

    list_filter = (
        "annee",
        "mois",
        "prestation",
        "prestataire",
        "tarif_personnalise",
    )

    search_fields = (
        "client__nom",
        "detail",
    )

    readonly_fields = (
        "montant_facture",
        "cout_total",
        "marge",
        "created_at",
        "updated_at",
    )