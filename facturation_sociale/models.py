from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from dossiers.models import Client


class TypePrestation(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    tarif_client_standard = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Tarif client standard",
    )
    actif = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre", "nom"]
        verbose_name = "Type de prestation"
        verbose_name_plural = "Types de prestations"

    def __str__(self):
        return self.nom


class PrestataireSocial(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    actif = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre", "nom"]
        verbose_name = "Prestataire social"
        verbose_name_plural = "Prestataires sociaux"

    def __str__(self):
        return self.nom


class TarifPrestataire(models.Model):
    prestation = models.ForeignKey(
        TypePrestation,
        on_delete=models.CASCADE,
        related_name="tarifs_prestataires",
    )
    prestataire = models.ForeignKey(
        PrestataireSocial,
        on_delete=models.CASCADE,
        related_name="tarifs_prestations",
    )
    cout_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="CoÃ»t unitaire",
    )
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["prestation__ordre", "prestation__nom", "prestataire__ordre"]
        constraints = [
            models.UniqueConstraint(
                fields=["prestation", "prestataire"],
                name="unique_tarif_prestataire_prestation",
            )
        ]
        verbose_name = "Tarif prestataire"
        verbose_name_plural = "Tarifs prestataires"

    def __str__(self):
        return (
            f"{self.prestation.nom} - "
            f"{self.prestataire.nom} : {self.cout_unitaire} â‚¬"
        )


class PrestationSociale(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="prestations_sociales",
    )

    prestation = models.ForeignKey(
        TypePrestation,
        on_delete=models.PROTECT,
        related_name="prestations_enregistrees",
    )

    prestataire = models.ForeignKey(
        PrestataireSocial,
        on_delete=models.PROTECT,
        related_name="prestations_enregistrees",
    )

    # PÃ©riode mÃ©tier : indÃ©pendante de la date de saisie.
    mois = models.PositiveSmallIntegerField()
    annee = models.PositiveSmallIntegerField()

    detail = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="SalariÃ© / dÃ©tail",
    )

    quantite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    # SNAPSHOT : ces montants sont figÃ©s lors de l'enregistrement.
    tarif_client_standard_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    tarif_client_applique = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    tarif_personnalise = models.BooleanField(default=False)

    motif_tarif_personnalise = models.CharField(
        max_length=255,
        blank=True,
    )

    # Coût standard configuré au moment de la saisie
    cout_prestataire_standard_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Coût prestataire standard",
    )

    # Coût réellement appliqué à cette prestation
    cout_prestataire_unitaire_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Coût prestataire appliqué",
    )

    # Indique qu'un coût exceptionnel a été saisi
    cout_prestataire_personnalise = models.BooleanField(
        default=False,
        verbose_name="Coût prestataire exceptionnel",
    )

    # Motif facultatif de l'exception
    motif_cout_prestataire_personnalise = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Motif du coût prestataire exceptionnel",
    )

    montant_facture = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    cout_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    marge = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-annee", "-mois", "client__nom", "prestation__nom"]
        verbose_name = "Prestation sociale"
        verbose_name_plural = "Prestations sociales"

    def save(self, *args, **kwargs):
        self.montant_facture = self.quantite * self.tarif_client_applique
        self.cout_total = (
            self.quantite * self.cout_prestataire_unitaire_snapshot
        )
        self.marge = self.montant_facture - self.cout_total

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.client.nom} - {self.prestation.nom} "
            f"- {self.mois:02d}/{self.annee}"
        )
