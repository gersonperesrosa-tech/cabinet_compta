"""Aides d'affichage (lecture seule) pour l'écran de saisie.

Les champs « affichés » du formset sont désactivés : ils ne sont jamais
envoyés et sont vides quand la page est réaffichée après une erreur. Ces
aides relisent les snapshots enregistrés afin que la page affiche les mêmes
valeurs standard que celles que le serveur réutilisera.
"""

from django import template

from ..models import PrestationSociale

register = template.Library()

MOIS = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet",
    "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def _ligne_id(form):
    try:
        return int(form["id"].value())
    except (TypeError, ValueError):
        return None


@register.simple_tag
def fs_references(formset, client, mois, annee):
    """Snapshots des lignes déjà enregistrées, indexés par identifiant."""
    ids = {pk for pk in (_ligne_id(form) for form in formset.forms) if pk}
    if not ids or client is None:
        return {}

    lignes = PrestationSociale.objects.filter(
        pk__in=ids, client=client, mois=mois, annee=annee
    )
    references = {}
    for ligne in lignes:
        references[ligne.pk] = {
            "prestation": str(ligne.prestation_id),
            "prestataire": str(ligne.prestataire_id),
            "std_client": str(ligne.tarif_client_standard_snapshot),
            "std_cout": str(ligne.cout_prestataire_standard_snapshot),
            # En mode standard, le serveur remplace le coût enregistré par le
            # snapshot standard. S'ils diffèrent, l'enregistrement le modifie.
            "cout_enregistre": str(ligne.cout_prestataire_unitaire_snapshot),
            "anomalie_cout": (
                not ligne.cout_prestataire_personnalise
                and ligne.cout_prestataire_standard_snapshot
                != ligne.cout_prestataire_unitaire_snapshot
            ),
        }
    return references


@register.filter
def fs_reference(references, form):
    if not isinstance(references, dict):
        return {}
    return references.get(_ligne_id(form), {})


@register.filter
def fs_anomalies(references):
    return sum(1 for ref in references.values() if ref["anomalie_cout"])


@register.filter
def fs_nom_mois(mois):
    try:
        return MOIS[int(mois)]
    except (TypeError, ValueError, IndexError):
        return ""
