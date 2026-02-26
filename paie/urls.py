from django.urls import path
from . import views_client, views_partenaire, views_cabinet
from .views import paie_client_dashboard



app_name = "paie"

urlpatterns = [

    # ----------------------------------------------------
    #   INTERFACE CLIENT
    # ----------------------------------------------------
    path("client/mois/<int:mois_id>/", views_client.mois_detail, name="client_mois_detail"),
    path("client/mois/<int:mois_id>/valider/", views_client.valider_mois, name="client_valider_mois"),
    path("client/mois/<int:mois_id>/salarie/<int:salarie_id>/", views_client.variables_salarie, name="client_variables_salarie"),
    path("client/salaries/", views_client.liste_salaries, name="client_salaries"),
    path("dashboard-client/", views_client.paie_client_dashboard, name="paie_client_dashboard"),


    # ----------------------------------------------------
    #   INTERFACE PARTENAIRE
    # ----------------------------------------------------
    path("partenaire/dashboard/", views_partenaire.partenaire_dashboard, name="partenaire_dashboard"),
    path("partenaire/clients/", views_partenaire.partenaire_liste_clients, name="partenaire_liste_clients"),
    path("partenaire/client/<int:client_id>/mois/", views_partenaire.partenaire_mois_client, name="partenaire_mois_client"),
    path("partenaire/mois/<int:paie_mois_id>/variables/", views_partenaire.partenaire_variables_mois, name="partenaire_variables_mois"),
    path("partenaire/mois/<int:paie_mois_id>/salarie/<int:salarie_id>/", views_partenaire.partenaire_detail_salarie_mois, name="partenaire_detail_salarie_mois"),
    path("partenaire/mois/<int:paie_mois_id>/bs-fait/", views_partenaire.partenaire_bs_fait, name="partenaire_bs_fait"),
    path("partenaire/mois/<int:paie_mois_id>/dsn-faite/", views_partenaire.partenaire_dsn_faite, name="partenaire_dsn_faite"),






    # ----------------------------------------------------
    #   INTERFACE CABINET
    # ----------------------------------------------------
    path("cabinet/", views_cabinet.dashboard_cabinet, name="cabinet_dashboard"),
    path("cabinet/clients-paie/", views_cabinet.clients_paie, name="cabinet_clients_paie"),
    path("cabinet/suivi-annuel/", views_cabinet.cabinet_suivi_annuel, name="cabinet_suivi_annuel"),




    # ----------------------------------------------------
    #   SALARIÉS (gestion côté cabinet)
    # ----------------------------------------------------
    path("cabinet/client/<int:client_id>/salaries/", views_cabinet.liste_salaries_client, name="cabinet_liste_salaries_client"),
    path("cabinet/client/<int:client_id>/salaries/ajouter/", views_cabinet.creer_salarie, name="cabinet_creer_salarie"),
    path("cabinet/salarie/<int:salarie_id>/modifier/", views_cabinet.modifier_salarie, name="cabinet_modifier_salarie"),
    path("cabinet/salarie/<int:salarie_id>/supprimer/", views_cabinet.supprimer_salarie, name="cabinet_supprimer_salarie"),

    # ----------------------------------------------------
    #   VARIABLES DE PAIE (gestion côté cabinet)
    # ----------------------------------------------------
    path("mois/<int:paie_mois_id>/variables/", 
         views_cabinet.variables_paie_salaries, 
         name="variables_paie_salaries"),

    path("mois/<int:paie_mois_id>/salarie/<int:salarie_id>/variables/", 
         views_cabinet.saisie_variables_salarie, 
         name="cabinet_saisie_variables_salarie"),

    # ----------------------------------------------------
    #   CREATION DU MOIS
    # ----------------------------------------------------

    path("cabinet/client/<int:client_id>/mois/creer/", views_cabinet.creer_mois_paie, name="cabinet_creer_mois_paie"),
    path("mois/<int:paie_mois_id>/valider/", views_cabinet.valider_mois_client, name="valider_mois_client"),
    path("client/mois/creer-suivant/", views_client.creer_mois_suivant, name="client_creer_mois_suivant"),
    path("mois/<int:paie_mois_id>/devalider/", views_cabinet.devalider_mois, name="devalider_mois"),



    # ----------------------------------------------------
    #  LISTE DES MOIS
    # ----------------------------------------------------

    path("client/<int:client_id>/mois/", views_cabinet.liste_mois_client, name="liste_mois_client"),
    path("mois/<int:paie_mois_id>/export-pdf/", views_cabinet.export_pdf_variables, name="export_pdf_variables"),
    path("mes-mois/", views_client.client_liste_mois, name="client_liste_mois"),
    path("cabinet/client/<int:client_id>/mois/creer-suivant/", views_cabinet.creer_mois_suivant, name="cabinet_creer_mois_suivant"),





]
