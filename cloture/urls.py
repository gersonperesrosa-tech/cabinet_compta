from django.urls import path
from . import views

urlpatterns = [
    # Gestion des années de clôture
    path("", views.cloture_home, name="cloture_home"),
    path("create/", views.cloture_create, name="cloture_create"),
    path("<int:cloture_id>/", views.cloture_detail, name="cloture_detail"),
    path("<int:cloture_id>/clients/", views.cloture_add_clients, name="cloture_add_clients"),
    path("<int:cloture_id>/remove-client/<int:client_id>/", views.cloture_remove_client, name="cloture_remove_client"),

    # Sous-module : révision
    path("revision/<int:module_id>/", views.revision_detail, name="revision_detail"),
    path("revisions/", views.gestion_revisions, name="gestion_revisions"),

    # Sous-module : plaquettes et liasse
    path("plaquettes-liasse/<int:module_id>/", views.plaquettes_liasse_detail, name="plaquettes_liasse_detail"),
    path("plaquettes-liasse/", views.gestion_plaquettes_liasse, name="gestion_plaquettes_liasse"),

    # Sous-module : cloture CA12
    path("ca12/", views.gestion_ca12, name="gestion_ca12"),
    path("ca12/<int:module_id>/", views.ca12_detail, name="ca12_detail"),

    # Sous-module : IS/CI
    path("isci/", views.gestion_isci, name="gestion_isci"),
    path("isci/<int:module_id>/", views.isci_detail, name="isci_detail"),

    # Sous-module : Cloture Déclarations
    path("declarations/", views.gestion_declarations, name="gestion_declarations"),
    path("declarations/<int:module_id>/", views.declarations_detail, name="declarations_detail"),

    # Sous-module : Cloture Missions
    path("mission/", views.gestion_mission, name="gestion_mission"),
    path("mission/<int:module_id>/", views.mission_detail, name="mission_detail"),

    # Sous-module : Cloture Juridique
    path("juridique/", views.gestion_juridique, name="gestion_juridique"),
    path("juridique/<int:module_id>/", views.juridique_detail, name="juridique_detail"),

    # Sous-module : Gestion globale
    path("global/", views.gestion_globale_cloture, name="gestion_globale_cloture"),

]
