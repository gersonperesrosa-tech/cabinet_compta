# Generated manually for the independent experimental closure table.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cloture", "0012_moduledeclarations_ca12_decl_cloture_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClotureExperimentaleLigne",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("statut_general", models.CharField(choices=[("non_commence", "Non commencé"), ("en_cours", "En cours"), ("termine", "Terminé")], default="non_commence", max_length=20)),
                ("version", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lignes_cloture_experimentales", to="dossiers.client")),
                ("cloture", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lignes_experimentales", to="cloture.clotureannee")),
            ],
            options={"ordering": ("client__nom",)},
        ),
        migrations.CreateModel(
            name="ClotureExperimentaleCellule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("colonne", models.CharField(max_length=40)),
                ("texte", models.TextField(blank=True, default="")),
                ("couleur", models.CharField(choices=[("none", "Sans couleur / blanc"), ("gray", "Gris"), ("yellow", "Jaune"), ("orange", "Orange"), ("light_green", "Vert clair"), ("dark_green", "Vert foncé"), ("red", "Rouge")], default="none", max_length=20)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("ligne", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cellules", to="cloture.clotureexperimentaleligne")),
            ],
        ),
        migrations.AddConstraint(
            model_name="clotureexperimentaleligne",
            constraint=models.UniqueConstraint(fields=("cloture", "client"), name="cloture_experimentale_ligne_unique"),
        ),
        migrations.AddConstraint(
            model_name="clotureexperimentalecellule",
            constraint=models.UniqueConstraint(fields=("ligne", "colonne"), name="cloture_experimentale_cellule_unique"),
        ),
    ]
