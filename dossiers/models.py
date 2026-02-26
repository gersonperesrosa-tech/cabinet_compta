from django.db import models
from django.contrib.auth.models import User



class Client(models.Model):

    # --- Choices ---
    REGIME_IMPOSITION_CHOICES = [
        ('IS', 'IS'),
        ('IR', 'IR'),
        ("RS", "Réel simplifié"),
        ("RN", "Réel normal"),
        ("MICRO", "Micro"),
        ("IR_CRL", "IR (CRL)"),
    ]

    REGIME_TVA_CHOICES = [
        ('CA3M', 'CA3 mensuelle'),
        ('CA3T', 'CA3 trimestrielle'),
        ('CA12', 'CA12'),
        ('FRANCHISE', 'Franchise'),
        ('EXO', 'Exonéré'),
    ]

    PERIODICITE_CHOICES = [
        ('MENSUEL', 'Mensuel'),
        ('TRIMESTRIEL', 'Trimestriel'),
        ('ANNUEL', 'Annuel'),
        ('REGULIER', 'Régulier'),
    ]

    # --- Liaison User <-> Client ---
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Utilisateur associé à ce client"
    )

    # --- Informations générales ---
    numero = models.IntegerField(null=True, blank=True)
    nom = models.CharField(max_length=255)
    forme_juridique = models.CharField(max_length=50)

    regime_imposition = models.CharField(
        max_length=20,
        choices=REGIME_IMPOSITION_CHOICES,
        null=True,
        blank=True
    )

    date_cloture = models.CharField(max_length=10, blank=True, null=True)

    regime_tva = models.CharField(
        max_length=20,
        choices=REGIME_TVA_CHOICES
    )

    periodicite = models.CharField(
        max_length=20,
        choices=PERIODICITE_CHOICES,
        null=True,
        blank=True,
        verbose_name="Périodicité de la saisie",
    )

    jour_echeance_tva = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text="Jour du mois pour l'échéance TVA (1 à 31)"
    )

    commentaires = models.TextField(blank=True)
    archive = models.BooleanField(default=False)

    # --- Modules activés ---
    module_saisie = models.BooleanField(default=False, verbose_name="Saisie comptable")
    module_tva = models.BooleanField(default=False)
    module_cfe = models.BooleanField(default=False, verbose_name="CFE")
    module_cvae = models.BooleanField(default=False, verbose_name="CVAE")
    module_tvs = models.BooleanField(default=False, verbose_name="TVS")
    module_cloture = models.BooleanField(default=False, verbose_name="Clôture")
    module_dividendes = models.BooleanField(default=False, verbose_name="Dividendes")
    module_social = models.BooleanField(default=False, verbose_name="Social")
    module_ir = models.BooleanField(default=False, verbose_name="IR personnel")
    module_suivi_mission = models.BooleanField(default=False, verbose_name="Suivi mission et LAB")

    # --- Nouveau module Paie ---
    module_paie = models.BooleanField(default=False, verbose_name="Module Paie")

    def __str__(self):
        return f"{self.numero} - {self.nom}"

class SuiviComptable(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    annee = models.IntegerField()

    date_maj_compta = models.DateField(null=True, blank=True)
    dernier_mois_traite = models.CharField(max_length=20, null=True, blank=True)
    periode_traitement = models.CharField(max_length=50, null=True, blank=True)
    verifie = models.BooleanField(default=False)
    saisi_par = models.CharField(max_length=100, null=True, blank=True)

    commentaire = models.TextField(null=True, blank=True)

    # 🔥 NOUVEAUX CHAMPS
    ca_actuel = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    saisie_en_cours = models.BooleanField(default=False)
    saisie_terminee = models.BooleanField(default=False)

    class Meta:
        unique_together = ('client', 'annee')
        verbose_name = "Suivi comptable"
        verbose_name_plural = "Suivis comptables"

    def __str__(self):
        return f"{self.client.nom} – {self.annee}"

from django.db import models
from django.core.exceptions import ValidationError

class TVA(models.Model):

    STATUT_CHOICES = [
        ("BLANC", "Blanc"),
        ("JAUNE", "Jaune"),
        ("VERT_CLAIR", "Vert clair"),
        ("VERT_FONCE", "Vert foncé"),
    ]

    client = models.ForeignKey("Client", on_delete=models.CASCADE, related_name="tvas")
    annee = models.IntegerField(default=2025)

    # Montants mensuels
    tva_janvier = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_fevrier = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_mars = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_avril = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_mai = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_juin = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_juillet = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_aout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_septembre = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_octobre = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_novembre = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tva_decembre = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Statuts mensuels
    statut_janvier = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_fevrier = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_mars = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_avril = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_mai = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_juin = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_juillet = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_aout = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_septembre = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_octobre = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_novembre = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)
    statut_decembre = models.CharField(max_length=20, choices=STATUT_CHOICES, null=True, blank=True)


    # Montants trimestriels (CA3T)
    tva_1t = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tva_2t = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tva_3t = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tva_4t = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Statuts trimestriels (CA3T)
    statut_1t = models.CharField(max_length=20, null=True, blank=True)
    statut_2t = models.CharField(max_length=20, null=True, blank=True)
    statut_3t = models.CharField(max_length=20, null=True, blank=True)
    statut_4t = models.CharField(max_length=20, null=True, blank=True)




    commentaires = models.TextField(blank=True)

    def __str__(self):
        return f"TVA – {self.client.nom} – {self.annee}"

    def regime_tva_client(self):
        return self.client.regime_tva
    regime_tva_client.short_description = "Régime TVA"



    # Nettoyage automatique des statuts
    def clean(self):
        champs_statuts = [
            "statut_janvier", "statut_fevrier", "statut_mars", "statut_avril",
            "statut_mai", "statut_juin", "statut_juillet", "statut_aout",
            "statut_septembre", "statut_octobre", "statut_novembre", "statut_decembre"
        ]

        for champ in champs_statuts:
            valeur = getattr(self, champ)
            if valeur in ["", " ", "None", "none", None]:
                setattr(self, champ, None)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class TVA_CA12(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    annee = models.IntegerField()

    montant_n_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    s1_07 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_s1_07 = models.CharField(max_length=20, null=True, blank=True)

    s2_12 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_s2_12 = models.CharField(max_length=20, null=True, blank=True)

    commentaire_tva_sup_1000 = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('client', 'annee')

    def __str__(self):
        return f"CA12 {self.client.nom} - {self.annee}"


class HistoriqueTVA(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    annee = models.IntegerField()

    # Régime TVA utilisé cette année-là
    regime_tva = models.CharField(
        max_length=20,
        choices=Client.REGIME_TVA_CHOICES
    )

    # -------------------------
    # Champs CA12
    # -------------------------
    ca12_montant_n_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca12_s1_07 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca12_s2_12 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    ca12_statut_s1_07 = models.CharField(max_length=20, null=True, blank=True)
    ca12_statut_s2_12 = models.CharField(max_length=20, null=True, blank=True)

    # -------------------------
    # Champs CA3T (Trimestriel)
    # -------------------------
    ca3t_t1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3t_t2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3t_t3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3t_t4 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    ca3t_statut_t1 = models.CharField(max_length=20, null=True, blank=True)
    ca3t_statut_t2 = models.CharField(max_length=20, null=True, blank=True)
    ca3t_statut_t3 = models.CharField(max_length=20, null=True, blank=True)
    ca3t_statut_t4 = models.CharField(max_length=20, null=True, blank=True)

    # -------------------------
    # Champs CA3M (Mensuel)
    # -------------------------
    ca3m_m1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m4 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m5 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m6 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m7 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m8 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m9 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m10 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m11 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ca3m_m12 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'annee')
        ordering = ['-annee']

    def __str__(self):
        return f"{self.client.nom} – {self.annee} ({self.regime_tva})"



class IS(models.Model):

    # 🔹 Client concerné
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='is_fiscaux'
    )

    # 🔹 Année fiscale (multi‑annuel)
    annee = models.IntegerField()

    # 🔹 Taux d'IS applicable
    taux_is = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # 🔹 Montant de la dernière déclaration
    derniere_declaration = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant de la dernière déclaration"
    )

    # 🔹 Prochaine échéance (date limite de paiement)
    prochaine_echeance = models.DateField(
        null=True,
        blank=True
    )

    # 🔹 Acomptes trimestriels
    acompte_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    acompte_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    acompte_3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    acompte_4 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # 🔹 Statuts colorés des acomptes (comme TVA)
    STATUTS = [
        ("BLANC", "Blanc"),
        ("JAUNE", "Jaune"),
        ("VERT_CLAIR", "Vert clair"),
        ("VERT_FONCE", "Vert foncé"),
    ]

    statut_acompte_1 = models.CharField(max_length=20, choices=STATUTS, default="BLANC")
    statut_acompte_2 = models.CharField(max_length=20, choices=STATUTS, default="BLANC")
    statut_acompte_3 = models.CharField(max_length=20, choices=STATUTS, default="BLANC")
    statut_acompte_4 = models.CharField(max_length=20, choices=STATUTS, default="BLANC")

    # 🔹 Solde d'IS
    solde_is = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # 🔹 Commentaires internes
    commentaires = models.TextField(blank=True)

    class Meta:
        unique_together = ('client', 'annee')
        verbose_name = "IS"
        verbose_name_plural = "IS fiscaux"

    def __str__(self):
        return f"IS – {self.client.nom} – {self.annee}"

    # --------------------------------------------------------------------
    # NOUVELLE STRUCTURE MODULES TVA
    # --------------------------------------------------------------------

class TVAAnnee(models.Model):
    annee = models.IntegerField(unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.annee)

class TVAModule(models.Model):
    TVA_TYPES = [
        ("CA3M", "Mensuel"),
        ("CA3T", "Trimestriel"),
        ("CA12", "Annuel"),
        ("FR", "Franchise"),
        ("EXO", "Exonéré"),
    ]

    annee = models.ForeignKey(TVAAnnee, on_delete=models.CASCADE, related_name="modules")
    type = models.CharField(max_length=10, choices=TVA_TYPES)

    def __str__(self):
        return f"{self.annee.annee} – {self.get_type_display()}"


from .models import TVAAnnee, TVAModule, Client

class TVAClientAnnee(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    annee = models.ForeignKey(TVAAnnee, on_delete=models.CASCADE)
    module = models.ForeignKey(TVAModule, on_delete=models.CASCADE, related_name="clients")

    class Meta:
        unique_together = ("client", "annee", "module")

    def __str__(self):
        return f"{self.client.nom} – {self.annee.annee} – {self.module}"

    @property
    def declaration(self):
        return self.declarations.first()

class TVADeclaration(models.Model):

    TVA_STATUTS = [
        ("NONE", "Sans pastille"),
        ("JAUNE", "A envoyer au client"),
        ("VERT_CLAIR", "Télétransmis"),
        ("VERT_FONCE", "Accepté"),
        ("BLANC", "Regeté"),

    ]

    tva_client_annee = models.ForeignKey(
        TVAClientAnnee,
        on_delete=models.CASCADE,
        related_name="declarations"
    )

    # -------------------------
    # CA3M (Mensuel)
    # -------------------------
    tva_janvier = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_janvier = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_fevrier = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_fevrier = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_mars = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_mars = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_avril = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_avril = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_mai = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_mai = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_juin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_juin = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_juillet = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_juillet = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_aout = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_aout = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_septembre = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_septembre = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_octobre = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_octobre = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_novembre = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_novembre = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_decembre = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_decembre = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    # -------------------------
    # CA3T (Trimestriel)
    # -------------------------
    ca3t_t1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_t1 = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    ca3t_t2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_t2 = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    ca3t_t3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_t3 = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    ca3t_t4 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_t4 = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    # -------------------------
    # CA12 (Annuel)
    # -------------------------
    tva_n_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    tva_acompte_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_acompte_1 = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_acompte_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_acompte_2 = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    tva_solde = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_solde = models.CharField(max_length=20, choices=TVA_STATUTS, default="NONE")

    commentaire_tva_plus_1000 = models.TextField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    # -------------------------------------------------------
    # MÉTHODES UTILITAIRES POUR LES TABLEAUX DE GESTION TVA
    # -------------------------------------------------------

    def get_mensuels(self):
        return [
            (self.tva_janvier, self.statut_janvier),
            (self.tva_fevrier, self.statut_fevrier),
            (self.tva_mars, self.statut_mars),
            (self.tva_avril, self.statut_avril),
            (self.tva_mai, self.statut_mai),
            (self.tva_juin, self.statut_juin),
            (self.tva_juillet, self.statut_juillet),
            (self.tva_aout, self.statut_aout),
            (self.tva_septembre, self.statut_septembre),
            (self.tva_octobre, self.statut_octobre),
            (self.tva_novembre, self.statut_novembre),
            (self.tva_decembre, self.statut_decembre),
        ]

    def get_trimestriels(self):
        return [
            (self.ca3t_t1, self.statut_t1),
            (self.ca3t_t2, self.statut_t2),
            (self.ca3t_t3, self.statut_t3),
            (self.ca3t_t4, self.statut_t4),
        ]

    def get_annuel(self):
        return {
            "n_1": self.tva_n_1,
            "acompte_1": (self.tva_acompte_1, self.statut_acompte_1),
            "acompte_2": (self.tva_acompte_2, self.statut_acompte_2),
            "solde": (self.tva_solde, self.statut_solde),
            "commentaire": self.commentaire_tva_plus_1000,
        }


    # -------------------------------------------------------
    # MODULE FICAL
    # -------------------------------------------------------


class ModuleFiscal(models.Model):
    nom = models.CharField(max_length=50, unique=True)  # IS, CFE, CVAE, TVS, DESDEB, Dividendes

    def __str__(self):
        return self.nom

class AnneeFiscale(models.Model):
    annee = models.IntegerField(unique=True)

    def __str__(self):
        return str(self.annee)

class ClientModuleFiscal(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    module = models.ForeignKey(ModuleFiscal, on_delete=models.CASCADE)
    annee = models.ForeignKey(AnneeFiscale, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("client", "module", "annee")

    def __str__(self):
        return f"{self.client.nom} – {self.module.nom} – {self.annee.annee}"



    # -------------------------------------------------------
    # NOUVEAU MODULE IS
    # -------------------------------------------------------

class ISDeclaration(models.Model):

    client_module = models.OneToOneField(
        ClientModuleFiscal,
        on_delete=models.CASCADE,
        related_name="is_declaration"
    )

    # Pré-remplis automatiquement
    is_n_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_n_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Acomptes
    acompte_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_acompte_1 = models.CharField(max_length=20, null=True, blank=True)

    acompte_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_acompte_2 = models.CharField(max_length=20, null=True, blank=True)

    acompte_3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_acompte_3 = models.CharField(max_length=20, null=True, blank=True)

    acompte_4 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_acompte_4 = models.CharField(max_length=20, null=True, blank=True)

    # Solde
    solde = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut_solde = models.CharField(max_length=20, null=True, blank=True)

    # Commentaire
    commentaire_plus_3000 = models.TextField(null=True, blank=True)

    def total_is(self):
        return sum([
            self.acompte_1 or 0,
            self.acompte_2 or 0,
            self.acompte_3 or 0,
            self.acompte_4 or 0,
            self.solde or 0
        ])

    # -------------------------------------------------------
    # MODULE CFE
    # -------------------------------------------------------

from django.db import models
from dossiers.models import ClientModuleFiscal

# --- CFE ---
STATUT_CHOICES = [
    ("NONE", "Sans pastille"),
    ("BLANC", "Blanc"),
    ("JAUNE", "Jaune"),
    ("VERT_CLAIR", "Vert clair"),
    ("VERT_FONCE", "Vert foncé"),
]

class CFEDeclaration(models.Model):
    client_module = models.OneToOneField(
        ClientModuleFiscal,
        on_delete=models.CASCADE,
        related_name="cfe_declaration"
    )

    # Montants
    cfe_n_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    acompte_cfe = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    solde_cfe = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Statuts
    statut_acompte = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="BLANC"
    )
    statut_solde = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="BLANC"
    )
    statut_1447c = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="BLANC"
    )

    # Informations complémentaires
    mode_paiement = models.CharField(max_length=100, blank=True)
    degrevement = models.CharField(max_length=255, blank=True)
    formulaire_1447c = models.CharField(max_length=255, blank=True)
    commentaire_plus_3000 = models.TextField(blank=True)

    @property
    def total_cfe(self):
        return (self.acompte_cfe or 0) + (self.solde_cfe or 0)

    def __str__(self):
        return f"CFE {self.client_module.client.nom} – {self.client_module.annee.annee}"

    # -------------------------------------------------------
    # MODULE CVAE
    # -------------------------------------------------------

class CVAEDeclaration(models.Model):
    client_module = models.OneToOneField(
        ClientModuleFiscal,
        on_delete=models.CASCADE,
        related_name="cvae_declaration"
    )

    cvae_n_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    acompte_cvae = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut_acompte_cvae = models.CharField(max_length=20, blank=True, null=True)

    solde_cvae = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut_solde_cvae = models.CharField(max_length=20, blank=True, null=True)

    commentaire_plus_1500 = models.TextField(blank=True, null=True)

    def total_cvae(self):
        return (self.acompte_cvae or 0) + (self.solde_cvae or 0)

    def __str__(self):
        return f"CVAE {self.client_module}"

    # -------------------------------------------------------
    # MODULE TVS
    # -------------------------------------------------------

class TVSDeclaration(models.Model):
    client_module = models.OneToOneField(
        ClientModuleFiscal,
        on_delete=models.CASCADE,
        related_name="tvs_declaration"
    )

    tvs_n_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    vehicule = models.BooleanField(default=False)
    soumis_tvs_n = models.BooleanField(default=False)

    formulaire = models.CharField(max_length=255, blank=True, null=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    statut_tvs = models.CharField(max_length=20, blank=True, null=True)

    info_vehicule = models.CharField(max_length=255, blank=True, null=True)
    date_achat = models.DateField(blank=True, null=True)
    date_cession = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"TVS {self.client_module}"

    # -------------------------------------------------------
    # MODULE DESDEB
    # -------------------------------------------------------

class DESDEBDeclaration(models.Model):
    client_module = models.OneToOneField(
        ClientModuleFiscal,
        on_delete=models.CASCADE,
        related_name="desdeclaration"
    )

    responsable = models.CharField(max_length=255, blank=True, null=True)
    retour_client = models.CharField(max_length=255, blank=True, null=True)

    # 12 mois
    ref_janvier = models.CharField(max_length=255, blank=True, null=True)
    statut_janvier = models.CharField(max_length=20, blank=True, null=True)

    ref_fevrier = models.CharField(max_length=255, blank=True, null=True)
    statut_fevrier = models.CharField(max_length=20, blank=True, null=True)

    ref_mars = models.CharField(max_length=255, blank=True, null=True)
    statut_mars = models.CharField(max_length=20, blank=True, null=True)

    ref_avril = models.CharField(max_length=255, blank=True, null=True)
    statut_avril = models.CharField(max_length=20, blank=True, null=True)

    ref_mai = models.CharField(max_length=255, blank=True, null=True)
    statut_mai = models.CharField(max_length=20, blank=True, null=True)

    ref_juin = models.CharField(max_length=255, blank=True, null=True)
    statut_juin = models.CharField(max_length=20, blank=True, null=True)

    ref_juillet = models.CharField(max_length=255, blank=True, null=True)
    statut_juillet = models.CharField(max_length=20, blank=True, null=True)

    ref_aout = models.CharField(max_length=255, blank=True, null=True)
    statut_aout = models.CharField(max_length=20, blank=True, null=True)

    ref_septembre = models.CharField(max_length=255, blank=True, null=True)
    statut_septembre = models.CharField(max_length=20, blank=True, null=True)

    ref_octobre = models.CharField(max_length=255, blank=True, null=True)
    statut_octobre = models.CharField(max_length=20, blank=True, null=True)

    ref_novembre = models.CharField(max_length=255, blank=True, null=True)
    statut_novembre = models.CharField(max_length=20, blank=True, null=True)

    ref_decembre = models.CharField(max_length=255, blank=True, null=True)
    statut_decembre = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"DESDEB {self.client_module}"

    # -------------------------------------------------------
    # MODULE DIVIDENDES
    # -------------------------------------------------------

class DividendesDeclaration(models.Model):
    client_module = models.OneToOneField(
        ClientModuleFiscal,
        on_delete=models.CASCADE,
        related_name="dividendes_declaration"
    )

    nom = models.CharField(max_length=255, blank=True, null=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    date_paiement = models.DateField(blank=True, null=True)
    date_2777d = models.DateField(blank=True, null=True)
    date_2561 = models.DateField(blank=True, null=True)

    annee_versement = models.CharField(max_length=10, blank=True, null=True)
    commentaires = models.TextField(blank=True, null=True)

    statut_dividendes = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Dividendes {self.client_module}"


    # -------------------------------------------------------
    # MODULE DP
    # -------------------------------------------------------

class DPDeclaration(models.Model):
    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name="dp"
    )

    dossier_deontologie = models.CharField(max_length=255, blank=True, null=True)
    acceptation_lab = models.CharField(max_length=255, blank=True, null=True)
    piece_identite = models.CharField(max_length=255, blank=True, null=True)
    statut = models.CharField(max_length=255, blank=True, null=True)
    bail = models.CharField(max_length=255, blank=True, null=True)
    lettre_mission = models.CharField(max_length=255, blank=True, null=True)
    avenant = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"DP {self.client.nom}"


    # -------------------------------------------------------
    # MODULE NOTE PRIVEE CLIENTS
    # -------------------------------------------------------

from django.db import models
from django.contrib.auth.models import User


class NoteTag(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    nom = models.CharField(max_length=50)

    def __str__(self):
        return self.nom


class NoteCategorie(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    nom = models.CharField(max_length=50)

    def __str__(self):
        return self.nom


class ClientNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    contenu = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    categorie = models.ForeignKey(NoteCategorie, null=True, blank=True, on_delete=models.SET_NULL)
    tags = models.ManyToManyField(NoteTag, blank=True)

    def tags_list(self):
        return ", ".join(t.nom for t in self.tags.all())

    def categorie_nom(self):
        return self.categorie.nom if self.categorie else ""

class UserNoteCategorie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


class UserNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    categorie = models.ForeignKey(UserNoteCategorie, on_delete=models.SET_NULL, null=True, blank=True)
    titre = models.CharField(max_length=200, blank=True)
    contenu = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


    # -------------------------------------------------------
    # MODULE KANBAN
    # -------------------------------------------------------

from django.db import models
from django.contrib.auth.models import User


class KanbanColumn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default="#cccccc")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.title


class KanbanTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default="#888888")

    def __str__(self):
        return self.name


class KanbanCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    column = models.ForeignKey(KanbanColumn, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.title


class KanbanCardTag(models.Model):
    card = models.ForeignKey(KanbanCard, on_delete=models.CASCADE)
    tag = models.ForeignKey(KanbanTag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("card", "tag")

# -------------------------------------------------------
# MODULE TODO LIST
# -------------------------------------------------------

from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta

class Todo(models.Model):

    PRIORITY_CHOICES = [
        ("low", "Faible"),
        ("normal", "Normale"),
        ("high", "Haute"),
    ]

    RECURRENCE_CHOICES = [
        ("none", "Aucune"),
        ("monthly_first", "Tous les 1er du mois"),
        ("monthly_day", "Tous les mois le jour choisi"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="normal"
    )

    due_date = models.DateField(null=True, blank=True)

    # Pour les rappels internes
    reminder_date = models.DateTimeField(null=True, blank=True)

    # Récurrence
    recurrence_type = models.CharField(
        max_length=20,
        choices=RECURRENCE_CHOICES,
        default="none"
    )

    # Utilisé uniquement si recurrence_type = "monthly_day"
    recurrence_day = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Jour du mois pour la récurrence"
    )

    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # -------------------------------
    #   MÉTHODES UTILES
    # -------------------------------

    def is_overdue(self):
        return self.due_date and not self.done and self.due_date < date.today()

    def is_today(self):
        return self.due_date == date.today()

    def is_tomorrow(self):
        return self.due_date == date.today() + timedelta(days=1)

    def __str__(self):
        return self.title


class SubTask(models.Model):
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(max_length=255)
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.title


    # -------------------------------
    #   MODULE DE CLOTURE
    # -------------------------------

class ClotureAnnee(models.Model):
    annee = models.PositiveIntegerField(unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.annee)

STATUT_CHOICES = [
    ("transparent", "Transparent"),
    ("jaune", "Jaune"),
    ("vert_clair", "Vert clair"),
    ("vert_fonce", "Vert foncé"),

]

class ClotureClient(models.Model):
    annee = models.ForeignKey(ClotureAnnee, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    date_maj = models.DateTimeField(auto_now=True)
    utilisateur_maj = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # -------------------------
    # SESSION REVISION
    # -------------------------
    revision_applicable = models.BooleanField(default=False)

    pre_revision = models.TextField(blank=True, null=True)
    pre_revision_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    relance_pieces = models.TextField(blank=True, null=True)
    relance_pieces_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    releve_decembre = models.TextField(blank=True, null=True)
    releve_decembre_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    revision = models.TextField(blank=True, null=True)
    revision_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    # -------------------------
    # SESSION PLAQUETTES & LIASSE
    # -------------------------
    plaquettes_applicable = models.BooleanField(default=False)

    plaquettes_envoi = models.TextField(blank=True, null=True)
    plaquettes_envoi_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    plaquettes_retour = models.TextField(blank=True, null=True)
    plaquettes_retour_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    liasse = models.TextField(blank=True, null=True)
    liasse_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    envoi_liasse = models.TextField(blank=True, null=True)
    envoi_liasse_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    ca_sup_152k = models.TextField(blank=True, null=True)

    # -------------------------
    # SESSION CA12
    # -------------------------
    ca12_applicable = models.BooleanField(default=False)

    ca12_faite = models.TextField(blank=True, null=True)
    ca12_faite_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    ca12_envoi = models.TextField(blank=True, null=True)
    ca12_envoi_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    ca12_tva_aic = models.TextField(blank=True, null=True)
    ca12_tva_aic_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    # -------------------------
    # SESSION IS / CI
    # -------------------------
    is_applicable = models.BooleanField(default=False)

    is_fait = models.TextField(blank=True, null=True)
    is_fait_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    is_envoi = models.TextField(blank=True, null=True)
    is_envoi_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    # -------------------------
    # SESSION CVAE
    # -------------------------
    cvae_applicable = models.BooleanField(default=False)

    cvae_1330_fait = models.TextField(blank=True, null=True)
    cvae_1330_fait_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    cvae_1130_envoi = models.TextField(blank=True, null=True)
    cvae_1130_envoi_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    cvae_1329def_fait = models.TextField(blank=True, null=True)
    cvae_1329def_fait_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    cvae_1329dev_envoi = models.TextField(blank=True, null=True)
    cvae_1329dev_envoi_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    # -------------------------
    # SESSION DECLOYER
    # -------------------------
    decloyer_applicable = models.BooleanField(default=False)

    decloyer_fait = models.TextField(blank=True, null=True)
    decloyer_fait_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    decloyer_envoi = models.TextField(blank=True, null=True)
    decloyer_envoi_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    # -------------------------
    # SESSION DAS2
    # -------------------------
    das2_applicable = models.BooleanField(default=False)

    das2 = models.TextField(blank=True, null=True)
    das2_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    # -------------------------
    # SESSION DRI
    # -------------------------
    dri_applicable = models.BooleanField(default=False)

    dri_fait = models.TextField(blank=True, null=True)
    dri_fait_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    dri_envoi = models.TextField(blank=True, null=True)
    dri_envoi_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    # -------------------------
    # SESSION MISSION
    # -------------------------
    mission_applicable = models.BooleanField(default=False)

    mission_lab = models.TextField(blank=True, null=True)
    mission_lab_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    mission_dossier = models.TextField(blank=True, null=True)
    mission_dossier_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    mission_attestation = models.TextField(blank=True, null=True)
    mission_attestation_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    mission_cr = models.TextField(blank=True, null=True)
    mission_cr_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    # -------------------------
    # SESSION JURIDIQUE
    # -------------------------
    juridique_applicable = models.BooleanField(default=False)

    juridique_fait = models.TextField(blank=True, null=True)
    juridique_fait_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    juridique_envoi_client = models.TextField(blank=True, null=True)
    juridique_envoi_client_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    juridique_retour_client = models.TextField(blank=True, null=True)
    juridique_retour_client_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    juridique_envoi_greffe = models.TextField(blank=True, null=True)
    juridique_envoi_greffe_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    juridique_validation_greffe = models.TextField(blank=True, null=True)
    juridique_validation_greffe_statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="transparent", blank=True)

    # ============================================================
    # MÉTHODES DE COMPTAGE DES STATUTS
    # ============================================================

    def _count_statuts(self, fields):
        statuts = [getattr(self, f) for f in fields]
        return {
            "transparent": statuts.count("transparent"),
            "jaune": statuts.count("jaune"),
            "vert_clair": statuts.count("vert_clair"),
            "vert_fonce": statuts.count("vert_fonce"),
            "total": len(statuts),
        }

    def revision_statuts_count(self):
        return self._count_statuts([
            "pre_revision_statut",
            "relance_pieces_statut",
            "releve_decembre_statut",
            "revision_statut",
        ])

    def plaquettes_statuts_count(self):
        return self._count_statuts([
            "plaquettes_envoi_statut",
            "plaquettes_retour_statut",
            "liasse_statut",
            "envoi_liasse_statut",
        ])

    def ca12_statuts_count(self):
        return self._count_statuts([
            "ca12_faite_statut",
            "ca12_envoi_statut",
            "ca12_tva_aic_statut",
        ])

    def is_statuts_count(self):
        return self._count_statuts([
            "is_fait_statut",
            "is_envoi_statut",
        ])

    def cvae_statuts_count(self):
        return self._count_statuts([
            "cvae_1330_fait_statut",
            "cvae_1130_envoi_statut",
            "cvae_1329def_fait_statut",
            "cvae_1329dev_envoi_statut",
        ])

    def decloyer_statuts_count(self):
        return self._count_statuts([
            "decloyer_fait_statut",
            "decloyer_envoi_statut",
        ])

    def das2_statuts_count(self):
        return self._count_statuts([
            "das2_statut",
        ])

    def dri_statuts_count(self):
        return self._count_statuts([
            "dri_fait_statut",
            "dri_envoi_statut",
        ])

    def mission_statuts_count(self):
        return self._count_statuts([
            "mission_lab_statut",
            "mission_dossier_statut",
            "mission_attestation_statut",
            "mission_cr_statut",
        ])

    def juridique_statuts_count(self):
        return self._count_statuts([
            "juridique_fait_statut",
            "juridique_envoi_client_statut",
            "juridique_retour_client_statut",
            "juridique_envoi_greffe_statut",
            "juridique_validation_greffe_statut",
        ])

    def __str__(self):
        return f"{self.client} – {self.annee}"

    class Meta:
        unique_together = ("annee", "client")
        ordering = ["annee", "client"]
