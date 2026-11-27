from decimal import Decimal

from django import forms
from django.db.models import Q

from .models import (
    PrestataireSocial,
    TarifPrestataire,
    TypePrestation,
)


TARIFICATION_CHOICES = [
    ("standard", "Tarif standard"),
    ("personnalise", "Tarif personnalisé"),
]


def get_tarif_prestataire_actif(prestation, prestataire):
    """Retourne le tarif utilisable pour une nouvelle combinaison."""
    return (
        TarifPrestataire.objects
        .filter(
            prestation=prestation,
            prestataire=prestataire,
            actif=True,
        )
        .first()
    )


class TypePrestationForm(forms.ModelForm):
    class Meta:
        model = TypePrestation
        fields = ["nom", "tarif_client_standard", "actif"]

        widgets = {
            "nom": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex. Bulletin de paie",
                }
            ),
            "tarif_client_standard": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "actif": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

        labels = {
            "nom": "Nom de la prestation",
            "tarif_client_standard": "Tarif client standard (€)",
            "actif": "Prestation active",
        }


class PrestataireSocialForm(forms.ModelForm):
    class Meta:
        model = PrestataireSocial
        fields = ["nom", "actif"]

        widgets = {
            "nom": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex. EB Paie",
                }
            ),
            "actif": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

        labels = {
            "nom": "Nom du prestataire",
            "actif": "Prestataire actif",
        }


class TarifPrestataireForm(forms.ModelForm):
    class Meta:
        model = TarifPrestataire
        fields = [
            "prestation",
            "prestataire",
            "cout_unitaire",
            "actif",
        ]

        widgets = {
            "prestation": forms.Select(
                attrs={"class": "form-select"}
            ),
            "prestataire": forms.Select(
                attrs={"class": "form-select"}
            ),
            "cout_unitaire": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "actif": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

        labels = {
            "prestation": "Prestation",
            "prestataire": "Prestataire",
            "cout_unitaire": "Coût unitaire (€)",
            "actif": "Tarif actif",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["prestation"].queryset = (
            TypePrestation.objects
            .filter(actif=True)
            .order_by("ordre", "nom")
        )

        self.fields["prestataire"].queryset = (
            PrestataireSocial.objects
            .filter(actif=True)
            .order_by("ordre", "nom")
        )


class PrestationLigneForm(forms.Form):
    """Une ligne de la saisie groupée des prestations sociales.

    Les prix affichés sont volontairement désactivés : le serveur recalcule
    toujours les snapshots à partir des règles métier et des exceptions.
    """

    id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    prestation = forms.ModelChoiceField(
        queryset=TypePrestation.objects.none(),
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    quantite = forms.DecimalField(
        min_value=Decimal("0.01"),
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control form-control-sm",
                "step": "0.01",
                "min": "0.01",
            }
        ),
    )
    detail = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Facultatif",
            }
        ),
    )
    prestataire = forms.ModelChoiceField(
        queryset=PrestataireSocial.objects.none(),
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )

    tarif_client_affiche = forms.DecimalField(
        required=False,
        disabled=True,
        widget=forms.NumberInput(
            attrs={"class": "form-control form-control-sm", "step": "0.01"}
        ),
    )
    cout_prestataire_affiche = forms.DecimalField(
        required=False,
        disabled=True,
        widget=forms.NumberInput(
            attrs={"class": "form-control form-control-sm", "step": "0.01"}
        ),
    )

    mode_tarification = forms.ChoiceField(
        choices=TARIFICATION_CHOICES,
        initial="standard",
        widget=forms.HiddenInput(),
    )
    tarif_client_personnalise = forms.DecimalField(
        required=False,
        min_value=Decimal("0.00"),
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs={"class": "form-control form-control-sm", "step": "0.01", "min": "0"}
        ),
    )
    motif_tarif_personnalise = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm"}),
    )
    mode_cout_prestataire = forms.ChoiceField(
        choices=TARIFICATION_CHOICES,
        initial="standard",
        widget=forms.HiddenInput(),
    )
    cout_prestataire_personnalise = forms.DecimalField(
        required=False,
        min_value=Decimal("0.00"),
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs={"class": "form-control form-control-sm", "step": "0.01", "min": "0"}
        ),
    )
    motif_cout_prestataire_personnalise = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm"}),
    )
    deja_facturee = forms.BooleanField(
        label="Déjà facturée (hors facturation mensuelle)",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "aria-label": "Déjà facturée (hors facturation mensuelle)",
            }
        ),
    )
    DELETE = forms.BooleanField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        historical_prestation_ids = kwargs.pop("historical_prestation_ids", [])
        historical_prestataire_ids = kwargs.pop("historical_prestataire_ids", [])
        super().__init__(*args, **kwargs)

        self.fields["prestation"].queryset = (
            TypePrestation.objects
            .filter(Q(actif=True) | Q(pk__in=historical_prestation_ids))
            .order_by("ordre", "nom")
        )
        self.fields["prestataire"].queryset = (
            PrestataireSocial.objects
            .filter(Q(actif=True) | Q(pk__in=historical_prestataire_ids))
            .order_by("ordre", "nom")
        )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("mode_tarification") == "personnalise":
            if cleaned_data.get("tarif_client_personnalise") is None:
                self.add_error(
                    "tarif_client_personnalise",
                    "Indiquez le prix unitaire exceptionnel.",
                )

        if cleaned_data.get("mode_cout_prestataire") == "personnalise":
            if cleaned_data.get("cout_prestataire_personnalise") is None:
                self.add_error(
                    "cout_prestataire_personnalise",
                    "Indiquez le coût unitaire exceptionnel.",
                )

        return cleaned_data
