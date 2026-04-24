from django import template

register = template.Library()

BADGE_STYLES = {
    "non_commence": ("bg-danger", "Non commencé"),
    "a_faire": ("bg-danger-subtle text-danger", "À faire"),
    "en_cours": ("bg-warning text-dark", "En cours"),
    "fait": ("bg-primary", "Fait"),

    "a_envoyer_client": ("bg-info text-dark", "À envoyer au client"),
    "en_attente_client": ("bg-secondary", "En attente du client"),

    "a_envoyer_admin": ("bg-info text-dark", "À envoyer à l'administration"),
    "envoye": ("bg-success", "Envoyé / Transmis"),
    "accepte": ("bg-success", "Accepté"),

    "na": ("bg-light text-dark border", "N/A"),
    "ne_pas_modifier": ("bg-dark text-white", "Ne pas modifier"),
}

@register.filter
def badge(statut):
    css, label = BADGE_STYLES.get(
        statut,
        ("bg-secondary", "-")  # Valeur par défaut
    )
    return f'<span class="badge {css}">{label}</span>'

@register.filter
def truncate10(value):
    if not value:
        return ""
    value = str(value).strip()
    return value[:10] + ("…" if len(value) > 10 else "")
