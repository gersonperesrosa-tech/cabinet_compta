from django import forms
from .models import Client, SuiviComptable, TVA, IS, ClotureClient, ClotureAnnee


class ClientForm(forms.ModelForm):

    class Meta:
        model = Client
        fields = "__all__"   # On garde tout le modèle

        labels = {
            "numero": "Numéro interne",
            "nom": "Nom du client",
            "forme_juridique": "Forme juridique",
            "regime_imposition": "Régime d’imposition",
            "date_cloture": "Date de clôture",
            "regime_tva": "Régime TVA",
            "periodicite": "Périodicité",
            "jour_echeance_tva": "Jour échéance TVA",
            "commentaires": "Notes internes",
            "archive": "Archivé",

            # Labels des modules
            "module_saisie": "Saisie comptable",
            "module_tva": "TVA",
            "module_cfe": "CFE",
            "module_cvae": "CVAE",
            "module_tvs": "TVS",
            "module_cloture": "Clôture",
            "module_dividendes": "Dividendes",
            "module_social": "Social",
            "module_ir": "IR personnel",
            "module_suivi_mission": "Suivi mission et LAB",
            "module_paie": "Module Paie",
        }

        widgets = {
            # Champs classiques
            "numero": forms.NumberInput(attrs={"class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "forme_juridique": forms.TextInput(attrs={"class": "form-control"}),

            "regime_imposition": forms.Select(attrs={"class": "form-select"}),
            "date_cloture": forms.TextInput(attrs={"class": "form-control"}),

            "regime_tva": forms.Select(attrs={"class": "form-select"}),
            "periodicite": forms.Select(attrs={"class": "form-select"}),

            "jour_echeance_tva": forms.NumberInput(attrs={"class": "form-control"}),

            "commentaires": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "archive": forms.CheckboxInput(attrs={"class": "form-check-input"}),

            # Widgets des modules (cases à cocher)
            "module_saisie": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "module_tva": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "module_cfe": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "module_cvae": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "module_tvs": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "module_cloture": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "module_dividendes": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "module_social": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "module_ir": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "module_suivi_mission": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "module_paie": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class SuiviComptableForm(forms.ModelForm):
    class Meta:
        model = SuiviComptable
        fields = [
            "date_maj_compta",
            "dernier_mois_traite",
            "saisi_par",
            "verifie",
	    "commentaire",
        ]

        widgets = {
            "date_maj_compta": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "dernier_mois_traite": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex : Janvier 2025"
            }),
            "saisi_par": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nom de la personne"
            }),
            "verifie": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }
class TVAForm(forms.ModelForm):

    fieldsets = [
        ("Déclaration TVA", {
            "fields": [
                ("annee", "statut_janvier"),
                ("tva_janvier", "statut_fevrier"),
                ("tva_fevrier", "statut_mars"),
                ("tva_mars", "statut_avril"),
                ("tva_avril", "statut_mai"),
                ("tva_mai", "statut_juin"),
                ("tva_juin", "statut_juillet"),
                ("tva_juillet", "statut_aout"),
                ("tva_aout", "statut_septembre"),
                ("tva_septembre", "statut_octobre"),
                ("tva_octobre", "statut_novembre"),
                ("tva_novembre", "statut_decembre"),
                "tva_decembre",  # ← IMPORTANT : chaîne simple, pas ("tva_decembre",)
            ]
        }),
        ("Commentaire interne", {
            "fields": ["commentaires"]
        }),
    ]

    class Meta:
        model = TVA
        exclude = ["client", "created_at", "updated_at"]

        labels = {
            "annee": "Année",
            "commentaires": "Commentaire interne",

            "tva_janvier": "TVA janvier",
            "tva_fevrier": "TVA février",
            "tva_mars": "TVA mars",
            "tva_avril": "TVA avril",
            "tva_mai": "TVA mai",
            "tva_juin": "TVA juin",
            "tva_juillet": "TVA juillet",
            "tva_aout": "TVA août",
            "tva_septembre": "TVA septembre",
            "tva_octobre": "TVA octobre",
            "tva_novembre": "TVA novembre",
            "tva_decembre": "TVA décembre",

            "statut_janvier": "Statut janvier",
            "statut_fevrier": "Statut février",
            "statut_mars": "Statut mars",
            "statut_avril": "Statut avril",
            "statut_mai": "Statut mai",
            "statut_juin": "Statut juin",
            "statut_juillet": "Statut juillet",
            "statut_aout": "Statut août",
            "statut_septembre": "Statut septembre",
            "statut_octobre": "Statut octobre",
            "statut_novembre": "Statut novembre",
            "statut_decembre": "Statut décembre",
        }

        widgets = {
            "annee": forms.NumberInput(attrs={"class": "form-control"}),

            **{
                f"tva_{m}": forms.NumberInput(
                    attrs={"class": "form-control", "step": "0.01"}
                )
                for m in [
                    "janvier", "fevrier", "mars", "avril", "mai", "juin",
                    "juillet", "aout", "septembre", "octobre", "novembre", "decembre"
                ]
            },

            **{
                f"statut_{m}": forms.Select(
                    attrs={"class": "form-select"}
                )
                for m in [
                    "janvier", "fevrier", "mars", "avril", "mai", "juin",
                    "juillet", "aout", "septembre", "octobre", "novembre", "decembre"
                ]
            },

            "commentaires": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class ISForm(forms.ModelForm):

    # Définition des fieldsets (structure logique)
    fieldsets = [
        ("Acomptes IS", {
            "fields": [
                ("acompte_1", "statut_acompte_1"),
                ("acompte_2", "statut_acompte_2"),
                ("acompte_3", "statut_acompte_3"),
                ("acompte_4", "statut_acompte_4"),
            ]
        }),
        ("Commentaire interne", {
            "fields": ["commentaires"]   # ← CORRECTION ICI
        }),
    ]

    class Meta:
        model = IS

        # On exclut les champs automatiques
        exclude = ["client", "annee", "created_at", "updated_at"]

        # Labels propres
        labels = {
            "acompte_1": "1er acompte",
            "statut_acompte_1": "Statut 1er acompte",

            "acompte_2": "2e acompte",
            "statut_acompte_2": "Statut 2e acompte",

            "acompte_3": "3e acompte",
            "statut_acompte_3": "Statut 3e acompte",

            "acompte_4": "4e acompte",
            "statut_acompte_4": "Statut 4e acompte",

            "commentaires": "Commentaire interne",   # ← CORRECTION ICI
        }

        # Widgets modernes
        widgets = {
            # Montants
            "acompte_1": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "acompte_2": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "acompte_3": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "acompte_4": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),

            # Statuts
            "statut_acompte_1": forms.Select(attrs={"class": "form-select"}),
            "statut_acompte_2": forms.Select(attrs={"class": "form-select"}),
            "statut_acompte_3": forms.Select(attrs={"class": "form-select"}),
            "statut_acompte_4": forms.Select(attrs={"class": "form-select"}),

            # Commentaire
            "commentaires": forms.Textarea(attrs={"class": "form-control", "rows": 3}),  # ← CORRECTION ICI
        }


class ClotureClientForm(forms.ModelForm):
    class Meta:
        model = ClotureClient
        fields = "__all__"
        exclude = ["annee", "client", "date_maj", "utilisateur_maj"]
