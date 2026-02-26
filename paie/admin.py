from django.contrib import admin
from .models import Salarie, PaieMois, VariablePaie


@admin.register(Salarie)
class SalarieAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "client", "date_entree", "date_sortie")
    list_filter = ("client", "date_entree")
    search_fields = ("nom", "prenom")


@admin.register(PaieMois)
class PaieMoisAdmin(admin.ModelAdmin):
    list_display = ("client", "mois", "annee", "client_valide", "partenaire_valide")
    list_filter = ("annee", "mois", "client_valide", "partenaire_valide")
    search_fields = ("client__nom",)


@admin.register(VariablePaie)
class VariablePaieAdmin(admin.ModelAdmin):
    list_display = (
        "salarie",
        "paie_mois",
        "heures_sup_25",
        "heures_sup_50",
        "primes",
        "conges_debut",
        "conges_fin",
        "absences_maladie",
        "absences_autres",
        "acomptes",
    )

    search_fields = ("salarie__nom", "salarie__prenom")
    list_filter = ("paie_mois__annee", "paie_mois__mois")
