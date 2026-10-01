from django.urls import path

from . import views

app_name = "facturation_sociale"

urlpatterns = [
    path(
        "prestation/<int:pk>/modifier/",
        views.modifier_prestation_sociale,
        name="modifier_prestation_sociale",
    ),
    path(
        "prestation/<int:pk>/supprimer/",
        views.supprimer_prestation_sociale,
        name="supprimer_prestation_sociale",
    ),
    path(
        "gestion/",
        views.gestion,
        name="gestion",
    ),
    path(
        "nouvelle-prestation/",
        views.nouvelle_prestation,
        name="nouvelle_prestation",
    ),
    path(
        "configurations/",
        views.configurations,
        name="configurations",
    ),

    # Prestations
    path(
        "configurations/prestations/",
        views.prestations,
        name="prestations",
    ),
    path(
        "configurations/prestations/<int:pk>/modifier/",
        views.modifier_prestation,
        name="modifier_prestation",
    ),

    # Prestataires
    path(
        "configurations/prestataires/",
        views.prestataires,
        name="prestataires",
    ),
    path(
        "configurations/prestataires/<int:pk>/modifier/",
        views.modifier_prestataire,
        name="modifier_prestataire",
    ),

    # Tarifs prestataires
    path(
        "configurations/tarifs-prestataires/",
        views.tarifs_prestataires,
        name="tarifs_prestataires",
    ),
    path(
        "configurations/tarifs-prestataires/<int:pk>/modifier/",
        views.modifier_tarif_prestataire,
        name="modifier_tarif_prestataire",
    ),
]

