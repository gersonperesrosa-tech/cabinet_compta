from dossiers.models import AnneeFiscale
from datetime import date
from .models import ClotureAnnee


def last_fiscal_year(request):
    current_year = date.today().year

    try:
        # On cherche l'année fiscale correspondant à l'année civile actuelle
        year_obj = AnneeFiscale.objects.get(annee=current_year)
        return {"last_year": year_obj.id}

    except AnneeFiscale.DoesNotExist:
        # Si l'année n'existe pas encore, on retombe sur la dernière année créée
        try:
            last_year_obj = AnneeFiscale.objects.latest("annee")
            return {"last_year": last_year_obj.id}
        except AnneeFiscale.DoesNotExist:
            return {"last_year": None}


def cloture_context(request):
    derniere_annee = ClotureAnnee.objects.order_by('-annee').first()
    return {
        "derniere_annee": derniere_annee
    }
