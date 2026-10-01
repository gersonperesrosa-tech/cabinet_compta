from datetime import date
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from dossiers.models import Client

from .models import (
    PrestataireSocial,
    PrestationSociale,
    TarifPrestataire,
    TypePrestation,
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


class NouvellePrestationForm(forms.Form):

    MOIS_CHOICES = [
        (1, "Janvier"),
        (2, "Février"),
        (3, "Mars"),
        (4, "Avril"),
        (5, "Mai"),
        (6, "Juin"),
        (7, "Juillet"),
        (8, "Août"),
        (9, "Septembre"),
        (10, "Octobre"),
        (11, "Novembre"),
        (12, "Décembre"),
    ]

    TARIFICATION_CHOICES = [
        ("standard", "Tarif standard"),
        ("personnalise", "Tarif personnalisé"),
    ]

    mois = forms.TypedChoiceField(
        label="Mois",
        choices=MOIS_CHOICES,
        coerce=int,
        widget=forms.Select(
            attrs={"class": "form-select"}
        ),
    )

    annee = forms.IntegerField(
        label="Année",
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(
            attrs={"class": "form-control"}
        ),
    )

    client = forms.ModelChoiceField(
        label="Client",
        queryset=Client.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_client",
            }
        ),
    )

    prestation = forms.ModelChoiceField(
        label="Prestation",
        queryset=TypePrestation.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_prestation",
            }
        ),
    )

    prestataire = forms.ModelChoiceField(
        label="Prestataire",
        queryset=PrestataireSocial.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_prestataire",
            }
        ),
    )

    detail = forms.CharField(
        label="Salarié / détail",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Facultatif - ex. Jean Dupont, simulation embauche...",
            }
        ),
    )

    quantite = forms.DecimalField(
        label="Quantité",
        min_value=Decimal("0.01"),
        decimal_places=2,
        max_digits=10,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "id": "id_quantite",
            }
        ),
    )

    mode_tarification = forms.ChoiceField(
        label="Tarification client",
        choices=TARIFICATION_CHOICES,
        initial="standard",
        widget=forms.RadioSelect(),
    )

    tarif_client_personnalise = forms.DecimalField(
        label="Prix unitaire personnalisé (€)",
        required=False,
        min_value=Decimal("0.00"),
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "id": "id_tarif_client_personnalise",
            }
        ),
    )

    motif_tarif_personnalise = forms.CharField(
        label="Motif du tarif personnalisé",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Facultatif - ex. tarif négocié",
            }
        ),
    )

    mode_cout_prestataire = forms.ChoiceField(
        label="Coût prestataire",
        choices=[
            ("standard", "Coût standard"),
            ("personnalise", "Coût exceptionnel"),
        ],
        initial="standard",
        widget=forms.RadioSelect(),
    )

    cout_prestataire_personnalise = forms.DecimalField(
        label="Coût unitaire exceptionnel (€)",
        required=False,
        min_value=Decimal("0.00"),
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "id": "id_cout_prestataire_personnalise",
            }
        ),
    )

    motif_cout_prestataire_personnalise = forms.CharField(
        label="Motif du coût exceptionnel",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Facultatif - ex. remise exceptionnelle",
                "id": "id_motif_cout_prestataire_personnalise",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = date.today()

        self.fields["mois"].initial = today.month
        self.fields["annee"].initial = today.year

        self.fields["client"].queryset = (
            Client.objects
            .filter(archive=False)
            .order_by("nom")
        )

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

        self.fields["client"].label_from_instance = (
            lambda obj:
            f"{obj.numero} - {obj.nom}"
            if obj.numero is not None
            else obj.nom
        )

    def clean(self):
        cleaned_data = super().clean()

        prestation = cleaned_data.get("prestation")
        prestataire = cleaned_data.get("prestataire")
        mode = cleaned_data.get("mode_tarification")
        tarif_personnalise = cleaned_data.get(
            "tarif_client_personnalise"
        )

        if prestation and prestataire:
            tarif_prestataire = (
                TarifPrestataire.objects
                .filter(
                    prestation=prestation,
                    prestataire=prestataire,
                    actif=True,
                )
                .first()
            )

            if not tarif_prestataire:
                raise ValidationError(
                    "Aucun tarif actif n'est configuré pour "
                    "cette prestation chez ce prestataire."
                )

            cleaned_data["tarif_prestataire_obj"] = (
                tarif_prestataire
            )

        if mode == "personnalise" and tarif_personnalise is None:
            self.add_error(
                "tarif_client_personnalise",
                "Indiquez le prix unitaire personnalisé.",
            )

        mode_cout_prestataire = cleaned_data.get(
            "mode_cout_prestataire"
        )
        cout_prestataire_personnalise = cleaned_data.get(
            "cout_prestataire_personnalise"
        )

        if (
            mode_cout_prestataire == "personnalise"
            and cout_prestataire_personnalise is None
        ):
            self.add_error(
                "cout_prestataire_personnalise",
                "Indiquez le coût unitaire exceptionnel.",
            )

        return cleaned_data


