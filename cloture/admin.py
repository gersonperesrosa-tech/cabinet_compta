from django.contrib import admin
from .models import (
    ClotureAnnee,
    ModuleRevision,
    ModulePlaquettesLiasse,
    ModuleDeclarations,
    ModuleMission,
    ModuleJuridique,
)

@admin.register(ClotureAnnee)
class ClotureAnneeAdmin(admin.ModelAdmin):
    list_display = ("annee", "date_creation")
    search_fields = ("annee",)
    filter_horizontal = ("clients",)


# ============================
# MODULE REVISION (a un champ termine)
# ============================
@admin.register(ModuleRevision)
class ModuleRevisionAdmin(admin.ModelAdmin):
    list_display = ("client", "cloture", "statut_general", "termine")
    list_filter = ("statut_general", "termine", "cloture")
    search_fields = ("client__nom",)


# ============================
# MODULE PLAQUETTES (pas de champ termine)
# ============================
@admin.register(ModulePlaquettesLiasse)
class ModulePlaquettesLiasseAdmin(admin.ModelAdmin):
    list_display = ("client", "cloture", "statut_general")
    list_filter = ("statut_general", "cloture")
    search_fields = ("client__nom",)


# ============================
# MODULE DECLARATIONS (pas de champ termine)
# ============================
@admin.register(ModuleDeclarations)
class ModuleDeclarationsAdmin(admin.ModelAdmin):
    list_display = ("client", "cloture", "statut_general")
    list_filter = ("statut_general", "cloture")
    search_fields = ("client__nom",)


# ============================
# MODULE MISSION (pas de champ termine)
# ============================
@admin.register(ModuleMission)
class ModuleMissionAdmin(admin.ModelAdmin):
    list_display = ("client", "cloture", "statut_general")
    list_filter = ("statut_general", "cloture")
    search_fields = ("client__nom",)


# ============================
# MODULE JURIDIQUE (pas de champ termine)
# ============================
@admin.register(ModuleJuridique)
class ModuleJuridiqueAdmin(admin.ModelAdmin):
    list_display = ("client", "cloture", "statut_general")
    list_filter = ("statut_general", "cloture")
    search_fields = ("client__nom",)
