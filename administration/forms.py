from django import forms
from django.contrib.auth.models import User, Group


class UserAddForm(forms.ModelForm):
    """
    Formulaire pour créer un utilisateur + choisir son groupe + statuts.
    """

    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Groupe",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    is_staff = forms.BooleanField(
        label="Statut équipe",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    is_superuser = forms.BooleanField(
        label="Super utilisateur",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "group",
            "is_staff",
            "is_superuser",
        ]

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)

        # Hash du mot de passe
        user.set_password(self.cleaned_data["password"])

        # Statuts
        user.is_staff = self.cleaned_data["is_staff"]
        user.is_superuser = self.cleaned_data["is_superuser"]

        if commit:
            user.save()

            # Assignation du groupe
            group = self.cleaned_data["group"]
            user.groups.set([group])

        return user


class UserEditForm(forms.ModelForm):

    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Groupe",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    is_active = forms.BooleanField(
        label="Compte actif",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    is_staff = forms.BooleanField(
        label="Statut équipe",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    is_superuser = forms.BooleanField(
        label="Super utilisateur",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "group",
            "is_active",
            "is_staff",
            "is_superuser",
        ]

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pré-remplissage automatique du groupe
        if self.instance.pk:
            user_groups = self.instance.groups.all()
            if user_groups.exists():
                self.fields["group"].initial = user_groups.first()

    def save(self, commit=True):
        user = super().save(commit=False)

        user.is_staff = self.cleaned_data["is_staff"]
        user.is_superuser = self.cleaned_data["is_superuser"]

        if commit:
            user.save()

            # Mise à jour du groupe
            group = self.cleaned_data["group"]
            user.groups.set([group])

        return user
