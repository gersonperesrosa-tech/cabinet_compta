from django.contrib import admin
from django.urls import path, include
from dossiers.views import CustomLoginView
from django.http import HttpResponse


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('', CustomLoginView.as_view(), name='login'),
    path('dossiers/', include('dossiers.urls')),
    path('paie/', include('paie.urls')),
    path("cloture/", include("cloture.urls")),
    path("admin-panel/", include("administration.urls")),
    path("cron/ping/", lambda request: HttpResponse("OK"), name="cron_ping"),

]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
