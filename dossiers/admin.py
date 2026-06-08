from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    # Colonnes affichées dans la liste
    list_display = (
        "numero",
        "nom",
        "forme_juridique",
        "regime_imposition",
        "regime_tva",
        "periodicite",
        "archive",
    )

    # Filtres latéraux
    list_filter = (
        "archive",
        "regime_imposition",
        "regime_tva",
        "periodicite",
    )

    # Barre de recherche
    search_fields = (
        "numero",
        "nom",
        "forme_juridique",
    )

    ordering = ("numero",)

    # Organisation du formulaire
    fieldsets = (
        ("Informations générales", {
            "fields": (
                "numero",
                "nom",
                "forme_juridique",
                "archive",
            )
        }),
        ("Fiscalité", {
            "fields": (
                "regime_imposition",
                "regime_tva",
                "periodicite",
                "jour_echeance_tva",
            )
        }),
        ("Notes", {
            "fields": ("commentaires",)
        }),
        ("Modules activés", {
            "fields": (
                "module_saisie",
                "module_tva",
                "module_cfe",
                "module_cvae",
                "module_tvs",
                "module_cloture",
                "module_dividendes",
                "module_social",
                "module_ir",
                "module_suivi_mission",
                "module_paie",
            )
        }),
    )
