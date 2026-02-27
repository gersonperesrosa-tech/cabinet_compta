from django.contrib import admin
from django.urls import path, include
from dossiers.views import CustomLoginView  # <-- importe ta vue

urlpatterns = [
    path('admin/', admin.site.urls),

    # Page d'accueil = page de login
    path('', CustomLoginView.as_view(), name='login'),

    # Routes existantes
    path('dossiers/', include('dossiers.urls')),
    path('paie/', include('paie.urls')),
]
