from django.contrib import admin
from django.urls import path, include
from dossiers import views as dossiers_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Page d'accueil (évite le 404 sur /)
    path('', dossiers_views.home, name='home'),

    # Routes des apps
    path('', include('dossiers.urls')),
    path('paie/', include('paie.urls')),
]
