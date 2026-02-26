from django.db import models
from dossiers.models import Client   # Ton modèle client actuel


# ----------------------------------------------------
#   SALARIÉ
# ----------------------------------------------------
class Salarie(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="salaries")

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField(null=True, blank=True)
    numero_securite_sociale = models.CharField(max_length=15, blank=True)

    date_entree = models.DateField(null=True, blank=True)
    date_sortie = models.DateField(null=True, blank=True)

    actif = models.BooleanField(default=True)

    mutuelle = models.CharField(max_length=200, blank=True)
    salaire_base = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.client.nom})"


class PaieMois(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    annee = models.IntegerField()
    mois = models.IntegerField()

    # Workflow existant
    client_valide = models.BooleanField(default=False)
    partenaire_valide = models.BooleanField(default=False)
    date_validation_client = models.DateTimeField(null=True, blank=True)
    date_validation_partenaire = models.DateTimeField(null=True, blank=True)

    # Nouveau suivi partenaire
    bs_fait = models.BooleanField(default=False)
    dsn_faite = models.BooleanField(default=False)

    date_bs_fait = models.DateTimeField(null=True, blank=True)
    date_dsn_faite = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("client", "annee", "mois")
        ordering = ["-annee", "-mois"]

    # Format long : Janvier, Février, ...
    @property
    def mois_nom(self):
        mois_noms = [
            "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        return mois_noms[self.mois]

    # Format court : Jan, Fév, Mar, ...
    @property
    def mois_nom_court(self):
        mois_noms = [
            "", "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
            "Juil", "Août", "Sep", "Oct", "Nov", "Déc"
        ]
        return mois_noms[self.mois]

    def __str__(self):
        return f"{self.mois_nom} {self.annee} – {self.client.nom}"



# ----------------------------------------------------
#   VARIABLES DE PAIE PAR SALARIÉ
# ----------------------------------------------------
class VariablePaie(models.Model):
    paie_mois = models.ForeignKey(PaieMois, on_delete=models.CASCADE)
    salarie = models.ForeignKey(Salarie, on_delete=models.CASCADE)

    heures_sup_25 = models.TextField(blank=True)
    heures_sup_50 = models.TextField(blank=True)
    primes = models.TextField(blank=True)
    conges_debut = models.TextField(blank=True)
    conges_fin = models.TextField(blank=True)
    absences_maladie = models.TextField(blank=True)
    absences_autres = models.TextField(blank=True)
    acomptes = models.TextField(blank=True)
    autres_infos = models.TextField(blank=True)

    class Meta:
        unique_together = ("paie_mois", "salarie")

    def __str__(self):
        return f"Variables {self.salarie} - {self.paie_mois.mois}/{self.paie_mois.annee}"

    # ----------------------------------------------------
    #   Invalidation automatique du mois si modification
    # ----------------------------------------------------
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        paie_mois = self.paie_mois

        # Si le mois était validé, on le remet en "à valider"
        if paie_mois.client_valide:
            paie_mois.client_valide = False
            paie_mois.date_validation_client = None
            paie_mois.save()
