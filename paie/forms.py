from django import forms
from .models import Salarie, VariablePaie


class SalarieForm(forms.ModelForm):
    class Meta:
        model = Salarie
        fields = "__all__"
        exclude = ("client",)

        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "numero_securite_sociale": forms.TextInput(attrs={"class": "form-control"}),
            "mutuelle": forms.TextInput(attrs={"class": "form-control"}),
            "salaire_base": forms.TextInput(attrs={"class": "form-control"}),
            "date_naissance": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "date_entree": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "date_sortie": forms.DateInput(attrs={"class": "form-control", "type": "date"}),

            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),

 
        }

    date_naissance = forms.DateField(required=False, input_formats=["%Y-%m-%d", "%d/%m/%Y"])
    date_entree = forms.DateField(required=False, input_formats=["%Y-%m-%d", "%d/%m/%Y"])
    date_sortie = forms.DateField(required=False, input_formats=["%Y-%m-%d", "%d/%m/%Y"])


class VariablePaieForm(forms.ModelForm):
    class Meta:
        model = VariablePaie
        fields = [
            "heures_sup_25",
            "heures_sup_50",
            "primes",
            "conges_debut",
            "conges_fin",
            "absences_maladie",
            "absences_autres",
            "acomptes",
            "autres_infos",
        ]

        widgets = {
            field: forms.Textarea(attrs={"class": "form-control", "rows": 2})
            for field in fields
        }

class DebloquerMoisForm(forms.Form):
    confirmation = forms.BooleanField(
        label="Autoriser le client à modifier les variables de paie",
        required=True
    )
