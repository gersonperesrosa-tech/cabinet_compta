from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views

from .views import (
    reset_suivi_comptable,

    # NOTES
    user_notes,
    add_user_note,
    edit_user_note,
    delete_user_note,
    add_user_note_categorie,

    # KANBAN
    kanban_board,
    add_kanban_column,
    rename_kanban_column,
    delete_kanban_column,
    move_kanban_column,
    add_kanban_card,
    edit_kanban_card,
    delete_kanban_card,
    move_kanban_card,
    add_kanban_tag,
    edit_kanban_tag,
    delete_kanban_tag,

    # TODO LIST
    todo_list,
    todo_add,
    todo_edit,
    todo_toggle,
    todo_delete,
    subtask_add,
    subtask_toggle,
    subtask_delete,

    # LOGIN / REGISTER
    CustomLoginView,
    RegisterView,

    # CLOTURE
    cloture_annees,
    cloture_clients,
    cloture_client_detail,
    cloture_annee_create,


)

urlpatterns = [
    # ============================
    # LOGIN / LOGOUT / REGISTER
    # ============================
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", RegisterView.as_view(), name="register"),


    # ============================
    # PASSWORD RESET
    # ============================
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="auth/password_reset.html"
        ),
        name="password_reset"
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html"
        ),
        name="password_reset_done"
    ),

    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html"
        ),
        name="password_reset_confirm"
    ),

    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),


    # ============================
    # ESPACE UTILISATEUR
    # ============================
    path("mon-espace/", views.user_space, name="user_space"),

    # ============================
    # Dashboard
    # ============================
    path("dashboard/", views.dashboard, name="dashboard"),

    # ============================
    # ajouter client
    # ============================

    path("clients/ajouter/", views.ajouter_client, name="ajouter_client"),


    # ============================
    # Notes personnelles
    # ============================
    path("mes-notes/", user_notes, name="user_notes"),
    path("mes-notes/ajouter/", add_user_note, name="add_user_note"),
    path("mes-notes/<int:note_id>/modifier/", edit_user_note, name="edit_user_note"),
    path("mes-notes/<int:note_id>/supprimer/", delete_user_note, name="delete_user_note"),
    path("mes-notes/categories/ajouter/", add_user_note_categorie, name="add_user_note_categorie"),

    # TODO LIST
    path('todo/', todo_list, name='todo_list'),
    path('todo/add/', todo_add, name='todo_add'),
    path('todo/edit/<int:todo_id>/', todo_edit, name='todo_edit'),
    path('todo/toggle/<int:todo_id>/', todo_toggle, name='todo_toggle'),
    path('todo/delete/<int:todo_id>/', todo_delete, name='todo_delete'),

    # Sous-tâches
    path('todo/subtask/add/<int:todo_id>/', subtask_add, name='subtask_add'),
    path('todo/subtask/toggle/<int:subtask_id>/', subtask_toggle, name='subtask_toggle'),
    path('todo/subtask/delete/<int:subtask_id>/', subtask_delete, name='subtask_delete'),

    # ============================
    # Notes clients
    # ============================
    path("client/<int:client_id>/notes/", views.client_notes, name="client_notes"),
    path("notes/<int:note_id>/edit/", views.edit_note, name="edit_note"),
    path("notes/<int:note_id>/delete/", views.delete_note, name="delete_note"),

    # Tags
    path("client/<int:client_id>/notes/add_tag/", views.add_tag, name="add_tag"),
    path("tags/<int:tag_id>/delete/", views.delete_tag, name="delete_tag"),

    # Catégories
    path("client/<int:client_id>/notes/add_categorie/", views.add_categorie, name="add_categorie"),
    path("categories/<int:cat_id>/delete/", views.delete_categorie, name="delete_categorie"),

    # Clients
    path("clients/", views.liste_clients, name="liste_clients"),
    path("clients/ajouter/", views.ajouter_client, name="ajouter_client"),
    path("clients/archives/", views.archives_clients, name="archives_clients"),
    path("clients/<int:client_id>/archiver/", views.archiver_client, name="archiver_client"),
    path("clients/<int:client_id>/supprimer/", views.supprimer_client, name="supprimer_client"),
    path("clients/<int:client_id>/restaurer/", views.restaurer_client, name="restaurer_client"),
    path("client/<int:client_id>/", views.fiche_client, name="fiche_client"),

    # TVA
    path("tva/historique/<int:client_id>/", views.historique_tva, name="historique_tva"),
    path("tva/ca3t/creer-annee-suivante/<int:annee>/", views.tva_ca3t_creer_annee_suivante, name="tva_ca3t_creer_annee_suivante"),


    # ============================
    # KANBAN
    # ============================

    # Vue principale
    path("kanban/", views.kanban_board, name="kanban_board"),

    # Colonnes
    path("kanban/colonnes/ajouter/", views.add_kanban_column, name="add_kanban_column"),
    path("kanban/colonnes/<int:column_id>/renommer/", views.rename_kanban_column, name="rename_kanban_column"),
    path("kanban/colonnes/<int:column_id>/supprimer/", views.delete_kanban_column, name="delete_kanban_column"),
    path("kanban/colonnes/<int:column_id>/deplacer/", views.move_kanban_column, name="move_kanban_column"),
    path("kanban/colonnes/<int:column_id>/couleur/", views.change_kanban_column_color, name="change_kanban_column_color"),
    path("kanban/colonnes/bulk/", views.move_kanban_column, name="move_kanban_column"),



    # Cartes
    path("kanban/cartes/ajouter/", views.add_kanban_card, name="add_kanban_card"),
    path("kanban/cartes/<int:card_id>/modifier/", views.edit_kanban_card, name="edit_kanban_card"),
    path("kanban/cartes/<int:card_id>/supprimer/", views.delete_kanban_card, name="delete_kanban_card"),
    path("kanban/cartes/<int:card_id>/deplacer/", views.move_kanban_card, name="move_kanban_card"),
    path("kanban/cartes/deplacer/", views.move_kanban_card, name="move_kanban_card"),


    # Tags
    path("kanban/tags/", views.kanban_tags, name="kanban_tags"),
    path("kanban/tags/ajouter/", views.add_kanban_tag, name="add_kanban_tag"),
    path("kanban/add_tag/", views.add_kanban_tag, name="add_kanban_tag"),
    path("kanban/tags/<int:tag_id>/modifier/", views.edit_kanban_tag, name="edit_kanban_tag"),
    path("kanban/tags/<int:tag_id>/supprimer/", views.delete_kanban_tag, name="delete_kanban_tag"),


    # AJAX assign/remove
    path("kanban/tags/assign/", views.assign_tag_to_card, name="assign_tag_to_card"),
    path("kanban/tags/remove/", views.remove_tag_from_card, name="remove_tag_from_card"),


    # ============================
    # Suivi comptable
    # ============================
    # Page liste
    path('suivi-comptable/', views.liste_suivi_comptable, name='liste_suivi_comptable'),

    # Popup AJAX
    path('suivi-comptable/popup/<int:client_id>/<int:annee>/', 
         views.popup_suivi_comptable, 
         name='popup_suivi_comptable'),

    # Page client + année
    path('client/<int:client_id>/suivi-comptable/<int:annee>/', 
         views.suivi_comptable, 
         name='suivi_comptable'),

    # Slidebar : formulaire AJAX
    path('suivi-comptable/formulaire/<int:client_id>/', 
         views.suivi_comptable_formulaire, 
         name='suivi_comptable_formulaire'),

    # Slidebar : sauvegarde AJAX
    path('suivi-comptable/save/<int:client_id>/', 
         views.suivi_comptable_save, 
         name='suivi_comptable_save'),

    # ============================
    # TVA – Déclarations
    # ============================

    # CA3 mensuelle – Page liste
    path('tva/ca3m/', 
         views.tva_ca3m, 
         name='tva_ca3m'),

    # CA3 mensuelle – Popup AJAX
    path('tva/ca3m/formulaire/<int:client_id>/', 
         views.tva_ca3m_formulaire, 
         name='tva_ca3m_formulaire'),

    path('tva/ca3m/save/<int:client_id>/', 
         views.tva_ca3m_save, 
         name='tva_ca3m_save'),

    path('tva/ca3m/creer-annee-suivante/<int:annee>/', 
    	 views.tva_ca3m_creer_annee_suivante, 
	 name='tva_ca3m_creer_annee_suivante'),


    # CA3 trimestrielle
    path('tva/ca3t/', 
         views.tva_ca3t, 
         name='tva_ca3t'),

    # TVA CA12
    path("tva/ca12/", views.tva_ca12, name="tva_ca12"),
    path("tva/ca12/popup/<int:client_id>/<int:annee>/", views.tva_ca12_popup, name="tva_ca12_popup"),
    path("tva/ca12/save/<int:client_id>/<int:annee>/", views.tva_ca12_save, name="tva_ca12_save"),
    path("tva/ca12/creer-annee-suivante/<int:annee>/", views.tva_ca12_creer_annee_suivante, name="tva_ca12_creer_annee_suivante"),

    # Franchise
    path("tva/franchise/", views.tva_franchise, name="tva_franchise"),

    # Exonéré
    path("tva/exoneres/", views.tva_exoneres, name="tva_exoneres"),

    # Ancienne route TVA (si encore utilisée quelque part)
    path('client/<int:client_id>/tva/<int:annee>/', 
         views.tva_view, 
         name='tva'),

    # Pastilles TVA (AJAX)
    path('tva/set-statut/', 
         views.tva_set_statut, 
         name='tva_set_statut'),

    # CA3 trimestrielle – Popup AJAX
    path('tva/ca3t/formulaire/<int:client_id>/<int:annee>/',
    views.tva_ca3t_formulaire,
    name='tva_ca3t_popup'),

    path('tva/ca3t/save/<int:client_id>/<int:annee>/',
    views.tva_ca3t_save,
    name='tva_ca3t_save'),

    # ============================
    # IS
    # ============================
    path('client/<int:client_id>/is/<int:annee>/', 
         views.is_view, 
         name='is'),

    path('client/<int:client_id>/is/<int:annee>/creer-suivante/', 
         views.is_creer_annee_suivante, 
         name='is_creer_annee_suivante'),


    # ============================
    # NOUVELLE STRUCTURE MODULES TVA
    # ============================

    path("tva/annees/", views.tva_annees, name="tva_annees"),
    path("tva/annees/creer/", views.tva_creer_annee, name="tva_creer_annee"),
    path("tva/annees/<int:annee_id>/modules/", views.tva_modules_annee, name="tva_modules_annee"),
    path("tva/module/<int:module_id>/clients/", views.tva_clients_module, name="tva_clients_module"),
    path("tva/module/<int:module_id>/clients/ajouter/", views.tva_clients_module_ajouter, name="tva_clients_module_ajouter"),
    path("tva/module/client/<int:client_annee_id>/supprimer/", views.tva_clients_module_supprimer, name="tva_clients_module_supprimer"),
    path("tva/module/client/<int:tva_client_annee_id>/ca3m/", views.tva_saisie_ca3m, name="tva_saisie_ca3m"),
    path("tva/module/client/<int:tva_client_annee_id>/ca3t/", views.tva_saisie_ca3t, name="tva_saisie_ca3t"),
    path("tva/module/client/<int:tva_client_annee_id>/ca12/", views.tva_saisie_ca12, name="tva_saisie_ca12"),
    path("tva/client/<int:client_id>/annee/<int:annee_id>/historique/", views.tva_historique_client, name="tva_historique_client"),

    # GESTION TVA PAR RÉGIME
    path("tva/gestion/ca3m/", views.tva_gestion_ca3m, name="tva_gestion_ca3m"),
    path("tva/gestion/ca3t/", views.tva_gestion_ca3t, name="tva_gestion_ca3t"),
    path("tva/gestion/ca12/", views.tva_gestion_ca12, name="tva_gestion_ca12"),
    path("tva/gestion/fr/", views.tva_gestion_fr, name="tva_gestion_fr"),
    path("tva/gestion/exo/", views.tva_gestion_exo, name="tva_gestion_exo"),
    path("suivi-comptable/reset/<int:annee>/", reset_suivi_comptable, name="reset_suivi_comptable"),

    # ============================
    # MODULE FISCAL
    # ============================

    path("fiscal/annees/", views.fiscal_annees, name="fiscal_annees"),
    path("fiscal/<int:annee_id>/modules/", views.fiscal_modules, name="fiscal_modules"),
    path("fiscal/<int:annee_id>/module/<int:module_id>/clients/", views.fiscal_clients_module, name="fiscal_clients_module"),
    path("fiscal/module/client/<int:cm_id>/supprimer/", views.fiscal_supprimer_client_module, name="fiscal_supprimer_client_module"),
    path("fiscal/is/saisie/<int:client_module_id>/", views.is_saisie, name="is_saisie"),
    path("fiscal/is/gestion/<int:annee_id>/", views.is_gestion, name="is_gestion"),
    path("cfe/gestion/<int:annee_id>/", views.cfe_gestion, name="cfe_gestion"),
    path("cfe/saisie/<int:client_module_id>/", views.cfe_saisie, name="cfe_saisie"),
    path("cvae/saisie/<int:client_module_id>/", views.cvae_saisie, name="cvae_saisie"),
    path("cvae/gestion/<int:annee_id>/", views.cvae_gestion, name="cvae_gestion"),
    path("tvs/saisie/<int:client_module_id>/", views.tvs_saisie, name="tvs_saisie"),
    path("tvs/gestion/<int:annee_id>/", views.tvs_gestion, name="tvs_gestion"),
    path("desdebs/saisie/<int:client_module_id>/", views.desdeb_saisie, name="desdeb_saisie"),
    path("desdebs/gestion/<int:annee_id>/", views.desdeb_gestion, name="desdeb_gestion"),
    path("dividendes/saisie/<int:client_module_id>/", views.dividendes_saisie, name="dividendes_saisie"),
    path("dividendes/gestion/<int:annee_id>/", views.dividendes_gestion, name="dividendes_gestion"),

    # ============================
    # MODULE DP
    # ============================

    path("dp/saisie/<int:client_id>/", views.dp_saisie, name="dp_saisie"),
    path("dp/gestion/", views.dp_gestion, name="dp_gestion"),

    # ============================
    # MODULE CLOTURE
    # ============================

    path("cloture/", cloture_annees, name="cloture_annees"),
    path("cloture/<int:annee_id>/", cloture_clients, name="cloture_clients"),
    path("cloture/client/<int:cloture_id>/", cloture_client_detail, name="cloture_client_detail"),
    path("cloture/annee/create/", cloture_annee_create, name="cloture_annee_create"),




]