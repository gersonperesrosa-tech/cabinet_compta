from django import template

register = template.Library()

@register.filter
def get_item(form, key):
    return form[key]

@register.filter
def empty_dash(value):
    """
    Retourne une chaîne vide si la valeur est None, vide ou zéro.
    Sinon retourne la valeur telle quelle.
    """
    if value in [None, "", " ", 0, 0.0]:
        return ""
    return value

@register.filter
def attr(obj, attr_name):
    """Permet d'accéder dynamiquement à un attribut dans un template."""
    try:
        return getattr(obj, attr_name)
    except:
        return ""