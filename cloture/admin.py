from django.contrib import admin
from .models import ClotureAnnee, ModuleRevision

@admin.register(ClotureAnnee)
class ClotureAnneeAdmin(admin.ModelAdmin):
    list_display = ("annee", "date_creation")
    search_fields = ("annee",)
    filter_horizontal = ("clients",)

@admin.register(ModuleRevision)
class ModuleRevisionAdmin(admin.ModelAdmin):
    list_display = ("client", "cloture", "statut_general", "termine")
    list_filter = ("statut_general", "termine", "cloture")
    search_fields = ("client__nom",)

