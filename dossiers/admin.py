from django.contrib import admin
from django.utils.html import format_html
from .models import Client

from .models import (
    Client,
    SuiviComptable,
    TVA,

    # Nouveaux modèles fiscaux
    ModuleFiscal,
    AnneeFiscale,
    ClientModuleFiscal,
    ISDeclaration,
    ClotureAnnee,
    ClotureClient
)


# ---------------------------------------------------------
#   CLIENT
# ---------------------------------------------------------
from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):

    list_display = (
        "numero",
        "nom",
        "forme_juridique",
        "regime_tva",
        "module_paie",
        "archive",
    )

    list_filter = (
        "regime_tva",
        "regime_imposition",
        "module_paie",
        "archive",
    )

    search_fields = (
        "nom",
        "numero",
        "forme_juridique",
        "user__username",
    )

    ordering = ("numero",)

    fieldsets = (
        ("Informations générales", {
            "fields": (
                "numero",
                "nom",
                "forme_juridique",
                "user",
                "archive",
            )
        }),

        ("Régimes fiscaux", {
            "fields": (
                "regime_imposition",
                "regime_tva",
                "periodicite",
                "jour_echeance_tva",
                "date_cloture",
            )
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
                "module_paie",   # ⭐ Nouveau module paie
            )
        }),

        ("Commentaires", {
            "fields": ("commentaires",),
        }),
    )


# ---------------------------------------------------------
#   SUIVI COMPTABLE (multi‑annuel)
# ---------------------------------------------------------
@admin.register(SuiviComptable)
class SuiviComptableAdmin(admin.ModelAdmin):
    list_display = (
        'client',
        'annee',
        'date_maj_compta',
        'dernier_mois_traite',
        'periode_traitement',
        'verifie',
    )
    list_filter = ('annee', 'verifie', 'periode_traitement')
    search_fields = ('client__nom',)
    ordering = ('client', 'annee')



# ---------------------------------------------------------
#   TVA (multi‑annuel)
# ---------------------------------------------------------
@admin.register(TVA)
class TVAAdmin(admin.ModelAdmin):

    readonly_fields = ("client", "regime_tva_client")

    list_display = (
        "client",
        "annee",
        "regime_tva_client",
        "tva_janvier", "pastille_janvier",
        "tva_fevrier", "pastille_fevrier",
        "tva_mars", "pastille_mars",
        "tva_avril", "pastille_avril",
        "tva_mai", "pastille_mai",
        "tva_juin", "pastille_juin",
        "tva_juillet", "pastille_juillet",
        "tva_aout", "pastille_aout",
        "tva_septembre", "pastille_septembre",
        "tva_octobre", "pastille_octobre",
        "tva_novembre", "pastille_novembre",
        "tva_decembre", "pastille_decembre",
    )

    list_filter = ("annee",)
    search_fields = ("client__nom",)
    ordering = ("client", "annee")

    fieldsets = (
        ("Informations client", {
            "fields": ("client", "regime_tva_client"),
        }),
        ("TVA mensuelle", {
            "fields": (
                ("tva_janvier", "statut_janvier"),
                ("tva_fevrier", "statut_fevrier"),
                ("tva_mars", "statut_mars"),
                ("tva_avril", "statut_avril"),
                ("tva_mai", "statut_mai"),
                ("tva_juin", "statut_juin"),
                ("tva_juillet", "statut_juillet"),
                ("tva_aout", "statut_aout"),
                ("tva_septembre", "statut_septembre"),
                ("tva_octobre", "statut_octobre"),
                ("tva_novembre", "statut_novembre"),
                ("tva_decembre", "statut_decembre"),
            ),
        }),
        ("Commentaires", {
            "fields": ("commentaires",),
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = TVA.objects.get(pk=obj.pk)
            obj.client = old_obj.client
        super().save_model(request, obj, form, change)

    # Pastilles cliquables
    def _pastille(self, obj, mois):
        statut = getattr(obj, f"statut_{mois}")
        couleurs = {
            "BLANC": "#FFFFFF",
            "JAUNE": "#FFD700",
            "VERT_CLAIR": "#90EE90",
            "VERT_FONCE": "#006400",
        }
        color = couleurs.get(statut, "#FFFFFF")

        return format_html(
            '<span class="tva-pastille" '
            'data-tva-id="{}" data-mois="{}" data-statut="{}" '
            'style="display:inline-block; width:12px; height:12px; border-radius:50%; '
            'border:1px solid #999; background-color:{}; cursor:pointer;"></span>',
            obj.pk, mois, statut, color
        )

    # Génération automatique des 12 pastilles
    def pastille_janvier(self, obj): return self._pastille(obj, "janvier")
    def pastille_fevrier(self, obj): return self._pastille(obj, "fevrier")
    def pastille_mars(self, obj): return self._pastille(obj, "mars")
    def pastille_avril(self, obj): return self._pastille(obj, "avril")
    def pastille_mai(self, obj): return self._pastille(obj, "mai")
    def pastille_juin(self, obj): return self._pastille(obj, "juin")
    def pastille_juillet(self, obj): return self._pastille(obj, "juillet")
    def pastille_aout(self, obj): return self._pastille(obj, "aout")
    def pastille_septembre(self, obj): return self._pastille(obj, "septembre")
    def pastille_octobre(self, obj): return self._pastille(obj, "octobre")
    def pastille_novembre(self, obj): return self._pastille(obj, "novembre")
    def pastille_decembre(self, obj): return self._pastille(obj, "decembre")

    class Media:
        js = ("cabinet_compta/js/tva_admin.js",)
        css = {
            "all": ("cabinet_compta/css/tva_admin.css",)
        }


    # --------------------------------------------------------------------
    # NOUVELLE STRUCTURE MODULES TVA
    # --------------------------------------------------------------------

from django.contrib import admin
from .models import TVAAnnee, TVAModule, TVAClientAnnee, TVADeclaration


# -----------------------------
# TVAAnnee
# -----------------------------
@admin.register(TVAAnnee)
class TVAAnneeAdmin(admin.ModelAdmin):
    list_display = ("annee", "date_creation")
    ordering = ("-annee",)
    search_fields = ("annee",)


# -----------------------------
# TVAModule
# -----------------------------
@admin.register(TVAModule)
class TVAModuleAdmin(admin.ModelAdmin):
    list_display = ("annee", "type")
    list_filter = ("annee", "type")
    search_fields = ("annee__annee", "type")
    ordering = ("annee__annee", "type")


# -----------------------------
# TVAClientAnnee
# -----------------------------
@admin.register(TVAClientAnnee)
class TVAClientAnneeAdmin(admin.ModelAdmin):
    list_display = ("client", "module", "get_annee", "get_type")
    list_filter = ("module__annee", "module__type")
    search_fields = ("client__nom", "module__annee__annee")

    def get_annee(self, obj):
        return obj.module.annee.annee
    get_annee.short_description = "Année"

    def get_type(self, obj):
        return obj.module.get_type_display()
    get_type.short_description = "Régime TVA"


# -----------------------------
# TVADeclaration
# -----------------------------
@admin.register(TVADeclaration)
class TVADeclarationAdmin(admin.ModelAdmin):
    list_display = ("tva_client_annee", "updated_at")
    list_filter = ("tva_client_annee__module__annee", "tva_client_annee__module__type")
    search_fields = ("tva_client_annee__client__nom",)
    ordering = ("-updated_at",)


# ---------------------------------------------------------
#   MODULES FISCAUX (nouvelle architecture)
# ---------------------------------------------------------

from .models import (
    ModuleFiscal,
    AnneeFiscale,
    ClientModuleFiscal,
    ISDeclaration,
)

@admin.register(ModuleFiscal)
class ModuleFiscalAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)
    ordering = ("nom",)


@admin.register(AnneeFiscale)
class AnneeFiscaleAdmin(admin.ModelAdmin):
    list_display = ("annee",)
    ordering = ("-annee",)
    search_fields = ("annee",)


@admin.register(ClientModuleFiscal)
class ClientModuleFiscalAdmin(admin.ModelAdmin):
    list_display = ("client", "module", "annee")
    list_filter = ("module", "annee")
    search_fields = ("client__nom",)
    ordering = ("annee", "module", "client")


@admin.register(ISDeclaration)
class ISDeclarationAdmin(admin.ModelAdmin):
    list_display = ("client_module", "total_is")
    list_filter = ("client_module__annee", "client_module__module")
    search_fields = ("client_module__client__nom",)
    ordering = ("client_module__annee", "client_module__client__nom")

@admin.register(ClotureAnnee)
class ClotureAnneeAdmin(admin.ModelAdmin):
    list_display = ("annee", "date_creation")

@admin.register(ClotureClient)
class ClotureClientAdmin(admin.ModelAdmin):
    list_display = ("client", "annee", "date_maj", "utilisateur_maj")
    list_filter = ("annee",)
    search_fields = ("client__nom", "client__prenom")

