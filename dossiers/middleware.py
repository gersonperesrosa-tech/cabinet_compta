from django.shortcuts import redirect
from django.urls import resolve

from dossiers.models import Client, TVAClientAnnee, ClientModuleFiscal

# Import des modules Clôture individuels
from cloture.models import (
    ModuleRevision,
    ModulePlaquettesLiasse,
    ModuleCA12,
    ModuleISCI,
    ModuleDeclarations,
    ModuleMission,
    ModuleJuridique,
)


class ClientArchiveMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        resolver = resolve(request.path)
        url_kwargs = resolver.kwargs

        client = None

        # 🔹 TVA : tva_client_annee_id
        if "tva_client_annee_id" in url_kwargs:
            try:
                obj = TVAClientAnnee.objects.get(id=url_kwargs["tva_client_annee_id"])
                client = obj.client
            except TVAClientAnnee.DoesNotExist:
                pass

        # 🔹 Fiscal : client_module_id
        if "client_module_id" in url_kwargs:
            try:
                obj = ClientModuleFiscal.objects.get(id=url_kwargs["client_module_id"])
                client = obj.client
            except ClientModuleFiscal.DoesNotExist:
                pass

        # 🔹 Clôture : module_id (module individuel)
        if "module_id" in url_kwargs:
            module_id = url_kwargs["module_id"]

            for Model in [
                ModuleRevision,
                ModulePlaquettesLiasse,
                ModuleCA12,
                ModuleISCI,
                ModuleDeclarations,
                ModuleMission,
                ModuleJuridique,
            ]:
                try:
                    obj = Model.objects.get(id=module_id)
                    client = obj.client
                    break
                except Model.DoesNotExist:
                    pass

        # 🔹 Accès direct via client_id
        if "client_id" in url_kwargs and client is None:
            try:
                client = Client.objects.get(id=url_kwargs["client_id"])
            except Client.DoesNotExist:
                pass

        # Si aucun client détecté → laisser passer
        if not client:
            return self.get_response(request)

        # Si client non archivé → laisser passer
        if not client.archive:
            return self.get_response(request)

        # 🔥 Désactiver automatiquement la paie
        if client.module_paie:
            client.module_paie = False
            client.save()

        # 🔥 Bloquer toute modification (POST)
        if request.method == "POST":
            return redirect("client_archive_interdit")

        return self.get_response(request)
