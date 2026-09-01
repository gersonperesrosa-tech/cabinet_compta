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

from django.contrib import admin
from dossiers.models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "client", "user", "app", "action")
    list_filter = ("app", "client", "user")
    search_fields = ("action", "metadata")
    ordering = ("-created_at",)


from django.contrib import admin
from django.apps import apps

app = apps.get_app_config("dossiers")  # le label de ton app (celui dans INSTALLED_APPS)

for model in app.get_models():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        # On ignore les modèles déjà enregistrés (Client, AuditLog, etc.)
        pass


from django.contrib import admin
from dossiers.models import (
    TVA_CA12,
    TVA,
    NoteTag,
    NoteCategorie,
    UserNoteCategorie,
    UserNote,
    KanbanColumn,
    KanbanTag,
    KanbanCard,
    KanbanCardTag,
    Todo,
    SubTask,
)

admin.site.unregister(TVA_CA12)
admin.site.unregister(TVA)
admin.site.unregister(NoteTag)
admin.site.unregister(NoteCategorie)
admin.site.unregister(UserNoteCategorie)
admin.site.unregister(UserNote)
admin.site.unregister(KanbanColumn)
admin.site.unregister(KanbanTag)
admin.site.unregister(KanbanCard)
admin.site.unregister(KanbanCardTag)
admin.site.unregister(Todo)
admin.site.unregister(SubTask)
