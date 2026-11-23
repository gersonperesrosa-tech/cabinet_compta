from django.db import models
from dossiers.models import Client


class ClotureStatus(models.TextChoices):
    NON_COMMENCE = "non_commence", "Non commencé"
    A_FAIRE = "a_faire", "À faire"
    EN_COURS = "en_cours", "En cours"
    FAIT = "fait", "Fait"
    A_ENVOYER_CLIENT = "a_envoyer_client", "À envoyer au client"
    EN_ATTENTE_CLIENT = "en_attente_client", "En attente du client"
    A_ENVOYER_ADMIN = "a_envoyer_admin", "À envoyer à l'administration"
    ENVOYE = "envoye", "Envoyé / Transmis"
    ACCEPTE = "accepte", "Accepté"
    NA = "na", "N/A"
    NE_PAS_MODIFIER = "ne_pas_modifier", "Ne pas modifier"
    TERMINE = "termine", "Terminé"

class ClotureAnnee(models.Model):
    annee = models.PositiveIntegerField()
    date_creation = models.DateTimeField(auto_now_add=True)
    clients = models.ManyToManyField(Client, related_name="clotures")

    def __str__(self):
        return str(self.annee)


# Les modèles ci-dessous sont volontairement indépendants des modules de
# clôture existants. Ils constituent le stockage de la maquette "tableau
# expérimental" et peuvent donc évoluer sans modifier les écrans actuels.
class ClotureExperimentaleLigne(models.Model):
    STATUT_NON_COMMENCE = "non_commence"
    STATUT_EN_COURS = "en_cours"
    STATUT_TERMINE = "termine"
    STATUT_CHOICES = (
        (STATUT_NON_COMMENCE, "Non commencé"),
        (STATUT_EN_COURS, "En cours"),
        (STATUT_TERMINE, "Terminé"),
    )

    cloture = models.ForeignKey(
        ClotureAnnee,
        on_delete=models.CASCADE,
        related_name="lignes_experimentales",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="lignes_cloture_experimentales",
    )
    statut_general = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default=STATUT_NON_COMMENCE,
    )
    # Version optimiste : une sauvegarde d'un onglet ancien ne peut pas écraser
    # silencieusement une modification plus récente.
    version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("cloture", "client"),
                name="cloture_experimentale_ligne_unique",
            )
        ]
        ordering = ("client__nom",)

    def __str__(self):
        return f"Expérimental — {self.client} ({self.cloture.annee})"


class ClotureExperimentaleCellule(models.Model):
    COULEUR_NONE = "none"
    COULEUR_GRAY = "gray"
    COULEUR_YELLOW = "yellow"
    COULEUR_ORANGE = "orange"
    COULEUR_LIGHT_GREEN = "light_green"
    COULEUR_DARK_GREEN = "dark_green"
    COULEUR_RED = "red"
    COULEUR_CHOICES = (
        (COULEUR_NONE, "Sans couleur / blanc"),
        (COULEUR_GRAY, "Gris"),
        (COULEUR_YELLOW, "Jaune"),
        (COULEUR_ORANGE, "Orange"),
        (COULEUR_LIGHT_GREEN, "Vert clair"),
        (COULEUR_DARK_GREEN, "Vert foncé"),
        (COULEUR_RED, "Rouge"),
    )

    ligne = models.ForeignKey(
        ClotureExperimentaleLigne,
        on_delete=models.CASCADE,
        related_name="cellules",
    )
    colonne = models.CharField(max_length=40)
    texte = models.TextField(blank=True, default="")
    couleur = models.CharField(max_length=20, choices=COULEUR_CHOICES, default=COULEUR_NONE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("ligne", "colonne"),
                name="cloture_experimentale_cellule_unique",
            )
        ]

    def __str__(self):
        return f"{self.ligne} — {self.colonne}"

class ClotureModuleBase(models.Model):
    cloture = models.ForeignKey(ClotureAnnee, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    statut_general = models.CharField(
        max_length=50,
        choices=ClotureStatus.choices,
        default=ClotureStatus.NON_COMMENCE
    )

    termine = models.BooleanField(default=False)

    class Meta:
        abstract = True


    # -------------------------
    # Module Révision + Plaquette et Liasse
    # -------------------------


class ModuleRevision(ClotureModuleBase):
    pre_revision = models.TextField(blank=True, null=True)
    statut_pre_revision = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True)

    relance_pieces = models.TextField(blank=True, null=True)
    statut_relance_pieces = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True)

    releve_bancaire = models.TextField(blank=True, null=True)
    statut_releve_bancaire = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True)

    revision_ad = models.TextField(blank=True, null=True)
    statut_revision_ad = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True)

    # 🆕 AJOUTER CECI
    plaquette_envoi_client = models.CharField(max_length=255, blank=True, null=True)
    statut_plaquette_envoi_client = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True)

    liasse_envoi_client = models.CharField(max_length=255, blank=True, null=True)
    statut_liasse_envoi_client = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True)


# -------------------------
# Module Plaquettes et liasses
# -------------------------

class ModulePlaquettesLiasse(models.Model):
    cloture = models.ForeignKey(ClotureAnnee, on_delete=models.CASCADE, related_name="plaquettes_liasse_modules")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    # Plaquette
    plaquette_envoi_client = models.CharField(max_length=255, blank=True, null=True)
    statut_plaquette_envoi_client = models.CharField(
        max_length=50,
        choices=ClotureStatus.choices,
        default="non_commence"
    )

    plaquette_retour_client = models.CharField(max_length=255, blank=True, null=True)
    statut_plaquette_retour_client = models.CharField(
        max_length=50,
        choices=ClotureStatus.choices,
        default="non_commence"
    )

    # Liasse
    liasse_envoi_client = models.CharField(max_length=255, blank=True, null=True)
    statut_liasse_envoi_client = models.CharField(
        max_length=50,
        choices=ClotureStatus.choices,
        default="non_commence"
    )

    liasse_retour_client = models.CharField(max_length=255, blank=True, null=True)
    statut_liasse_retour_client = models.CharField(
        max_length=50,
        choices=ClotureStatus.choices,
        default="non_commence"
    )

    # CA > 152 500 €
    ca_152500 = models.CharField(max_length=255, blank=True, null=True)

    # Statut général
    statut_general = models.CharField(
        max_length=50,
        choices=ClotureStatus.choices,
        default="non_commence"
    )

    def __str__(self):
        return f"Plaquettes & Liasse – {self.client.nom} ({self.cloture.annee})"


# -------------------------
# Module ClotureCA12
# -------------------------

class ModuleCA12(models.Model):
    cloture = models.ForeignKey(ClotureAnnee, on_delete=models.CASCADE, related_name="ca12_modules")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    ca12_faite = models.CharField(max_length=255, blank=True, null=True)
    statut_ca12_faite = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    ca12_envoyee = models.CharField(max_length=255, blank=True, null=True)
    statut_ca12_envoyee = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    statut_general = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    def __str__(self):
        return f"CA12 – {self.client.nom} ({self.cloture.annee})"

# -------------------------
# Module IS/CI
# -------------------------

class ModuleISCI(models.Model):
    cloture = models.ForeignKey(ClotureAnnee, on_delete=models.CASCADE, related_name="isci_modules")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    is_fait = models.CharField(max_length=255, blank=True, null=True)
    statut_is_fait = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    is_envoi = models.CharField(max_length=255, blank=True, null=True)
    statut_is_envoi = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    statut_general = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    def __str__(self):
        return f"IS/CI – {self.client.nom} ({self.cloture.annee})"

# -------------------------
# Module Cloture Déclarations
# -------------------------

class ModuleDeclarations(models.Model):
    cloture = models.ForeignKey(ClotureAnnee, on_delete=models.CASCADE, related_name="declarations_modules")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    # VA-1330 CVAE
    va1330_fait = models.CharField(max_length=255, blank=True, null=True)
    statut_va1330_fait = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

    va1330_envoi = models.CharField(max_length=255, blank=True, null=True)
    statut_va1330_envoi = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

    # CVAE 1329DEF
    cvae1329_fait = models.CharField(max_length=255, blank=True, null=True)
    statut_cvae1329_fait = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

    cvae1329_envoi = models.CharField(max_length=255, blank=True, null=True)
    statut_cvae1329_envoi = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

    # DECLOYER
    decloyer_fait = models.CharField(max_length=255, blank=True, null=True)
    statut_decloyer_fait = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

    # DAS2
    das2_fait = models.CharField(max_length=255, blank=True, null=True)
    statut_das2_fait = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

    # DRI
    dri_fait = models.CharField(max_length=255, blank=True, null=True)
    statut_dri_fait = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

    dri_envoi = models.CharField(max_length=255, blank=True, null=True)
    statut_dri_envoi = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

    ca12_decl_cloture = models.CharField(max_length=255, blank=True, null=True)
    statut_ca12_decl_cloture = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

    is_decl_cloture = models.CharField(max_length=255, blank=True, null=True)
    statut_is_decl_cloture = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

    # Statut général
    statut_general = models.CharField(max_length=50, choices=ClotureStatus.choices, blank=True, null=True, default="non_commence")

# -------------------------
# Module Cloture Missions
# -------------------------

class ModuleMission(models.Model):
    cloture = models.ForeignKey(ClotureAnnee, on_delete=models.CASCADE, related_name="mission_modules")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    lab_maintien = models.CharField(max_length=255, blank=True, null=True)
    statut_lab_maintien = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    dossier_travail = models.CharField(max_length=255, blank=True, null=True)
    statut_dossier_travail = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    attestation = models.CharField(max_length=255, blank=True, null=True)
    statut_attestation = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    cr_mission = models.CharField(max_length=255, blank=True, null=True)
    statut_cr_mission = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    statut_general = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    def __str__(self):
        return f"Mission – {self.client.nom} ({self.cloture.annee})"


# -------------------------
# Module Juridique
# -------------------------

class ModuleJuridique(models.Model):
    cloture = models.ForeignKey(ClotureAnnee, on_delete=models.CASCADE, related_name="juridique_modules")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    juridique_fait = models.CharField(max_length=255, blank=True, null=True)
    statut_juridique_fait = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    juridique_envoi_client = models.CharField(max_length=255, blank=True, null=True)
    statut_juridique_envoi_client = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    retour_client = models.CharField(max_length=255, blank=True, null=True)
    statut_retour_client = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    envoi_greffe = models.CharField(max_length=255, blank=True, null=True)
    statut_envoi_greffe = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    validation_greffe = models.CharField(max_length=255, blank=True, null=True)
    statut_validation_greffe = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    statut_general = models.CharField(max_length=50, choices=ClotureStatus.choices, default="non_commence")

    def __str__(self):
        return f"Juridique – {self.client.nom} ({self.cloture.annee})"
