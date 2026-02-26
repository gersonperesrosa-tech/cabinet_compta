from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Inclusion de l'app Django réelle
    path('', include('dossiers.urls')),
    path("paie/", include("paie.urls")),

]
