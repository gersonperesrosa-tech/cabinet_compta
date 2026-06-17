from django import template

register = template.Library()

@register.filter
def strip_zeros(value):
    if value in (None, ""):
        return ""
    try:
        f = float(value)
        return ('%f' % f).rstrip('0').rstrip('.')
    except:
        return value

@register.filter
def format_tva(value):
    """
    Formate les montants TVA :
    - supprime .00
    - supprime les zéros inutiles
    - ajoute des espaces pour les milliers
    """
    if value in (None, ""):
        return ""

    try:
        # Convertit en float
        f = float(value)

        # Supprime les zéros inutiles
        cleaned = ('%f' % f).rstrip('0').rstrip('.')

        # Séparation des milliers avec espace
        if '.' in cleaned:
            entier, decimal = cleaned.split('.')
            entier = f"{int(entier):,}".replace(",", " ")
            return f"{entier}.{decimal}"
        else:
            return f"{int(cleaned):,}".replace(",", " ")

    except:
        return value

@register.simple_tag
def seuil_depasse(module, code, valeur):
    """
    Retourne True si la valeur dépasse le seuil défini en base.
    """
    from dossiers.models import SeuilFiscal

    # Valeurs vides → pas de dépassement
    if valeur in (None, "", "-", "0", "0.00"):
        return False

    # Conversion en nombre
    try:
        val = float(str(valeur).replace(" ", "").replace(",", "."))
    except:
        return False

    # Récupération du seuil
    try:
        seuil = SeuilFiscal.objects.get(module=module, code=code).valeur
        return val > float(seuil)
    except SeuilFiscal.DoesNotExist:
        return False


@register.simple_tag
def seuil_style(module, code, valeur):
    """
    Retourne le HTML du montant avec gras + icône si seuil dépassé,
    mais texte en noir.
    """
    from django.utils.safestring import mark_safe
    from dossiers.models import SeuilFiscal

    # Formatage du montant
    try:
        val_float = float(str(valeur).replace(" ", "").replace(",", "."))
        formatted = f"{val_float:,.2f}".replace(",", " ").replace(".", ",")
    except:
        formatted = valeur
        val_float = None

    # Vérification du seuil
    depasse = False
    try:
        seuil = SeuilFiscal.objects.get(module=module, code=code).valeur
        if val_float is not None:
            depasse = val_float > float(seuil)
    except:
        pass

    # Style si dépassement (texte noir)
    if depasse:
        html = f"""
            <span class="fw-bold text-dark">
                {formatted}
                <i class="bi bi-exclamation-triangle-fill text-warning ms-1"></i>
            </span>
        """
    else:
        html = f"{formatted}"

    return mark_safe(html)
