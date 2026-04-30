import csv
from django.contrib import admin, messages
from django.shortcuts import render
from django.urls import path
from .models import Client
from .utils import parse_bool  # si tu as une fonction utilitaire

class ClientImportAdmin(admin.ModelAdmin):
    change_list_template = "admin/client_import.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-clients/", self.admin_site.admin_view(self.import_clients), name="import_clients"),
        ]
        return custom_urls + urls

    def import_clients(self, request):
        if request.method == "POST" and request.FILES.get("csv_file"):
            file = request.FILES["csv_file"].read().decode("utf-8").splitlines()
            reader = csv.DictReader(file)

            count = 0
            for row in reader:
                Client.objects.update_or_create(
                    numero=row.get("numero"),
                    defaults={
                        "nom": row.get("nom"),
                        "forme_juridique": row.get("forme_juridique") or None,
                        "regime_imposition": row.get("regime_imposition") or None,
                        "date_cloture": row.get("date_cloture") or None,
                        "regime_tva": row.get("regime_tva"),
                        "periodicite": row.get("periodicite") or None,
                        "jour_echeance_tva": row.get("jour_echeance_tva") or None,
                        "commentaires": row.get("commentaires") or "",
                        "archive": parse_bool(row.get("archive")),
                        "module_saisie": parse_bool(row.get("module_saisie")),
                        "module_tva": parse_bool(row.get("module_tva")),
                        "module_cfe": parse_bool(row.get("module_cfe")),
                        "module_cvae": parse_bool(row.get("module_cvae")),
                        "module_tvs": parse_bool(row.get("module_tvs")),
                        "module_cloture": parse_bool(row.get("module_cloture")),
                        "module_dividendes": parse_bool(row.get("module_dividendes")),
                        "module_social": parse_bool(row.get("module_social")),
                        "module_ir": parse_bool(row.get("module_ir")),
                        "module_suivi_mission": parse_bool(row.get("module_suivi_mission")),
                        "module_paie": parse_bool(row.get("module_paie")),
                    }
                )
                count += 1

            messages.success(request, f"{count} clients importés avec succès.")
            return render(request, "admin/client_import_done.html")

        return render(request, "admin/client_import_form.html")
