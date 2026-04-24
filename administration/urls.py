from django.urls import path
from . import views

urlpatterns = [
    path("users/", views.users_list, name="admin_users_list"),
    path("users/add/", views.user_add, name="admin_user_add"),
    path("users/<int:user_id>/edit/", views.user_edit, name="admin_user_edit"),
    path("users/<int:user_id>/toggle/", views.user_toggle_active, name="admin_user_toggle"),
    path("users/<int:user_id>/delete/", views.user_delete, name="admin_user_delete"),    
    path("groups/", views.groups_list, name="admin_groups_list"),
    path("groups/<int:group_id>/edit/", views.group_edit, name="admin_group_edit"),
    path("access-denied/", views.access_denied, name="access_denied"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("emails/", views.email_logs_list, name="email_logs_list"),

    
]
