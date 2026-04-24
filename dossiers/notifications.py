from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import NotificationEmail, EmailLog


def envoyer_email(event, template_name, subject, context):
    emails = NotificationEmail.objects.filter(event=event).values_list("email", flat=True)
    if not emails:
        return

    # Identité visuelle experteaprovence
    context.update({
        "brand_name": "experteaprovence",
        "brand_color": "#013363",
        "brand_logo": "https://gestionexpertea.wordpress.com/wp-content/uploads/2026/04/gestionexpertea.jpg",
        "subject": subject,
        "preheader": context.get("preheader", ""),
    })

    html_message = render_to_string(template_name, context)
    text_message = "Une nouvelle action a été effectuée. Consultez votre espace cabinet."

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email="gerson.peresdarosa@expertea-provence.fr",
            to=list(emails),
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()

        for email in emails:
            EmailLog.objects.create(event=event, destinataire=email, message=subject)

    except Exception as e:
        for email in emails:
            EmailLog.objects.create(event=event, destinataire=email, message=str(e), statut="échec")


def envoyer_notifications_paie(mois):
    envoyer_email(
        event="PAIE_VALIDEE",
        template_name="emails/paie_validee.html",
        subject=f"Paie validée – {mois.client} – {mois.mois}/{mois.annee}",
        context={
            "mois": mois,
            "preheader": f"Le mois de paie {mois.mois}/{mois.annee} a été validé pour {mois.client}."
        },
    )


def envoyer_notifications_bs(mois):
    envoyer_email(
        event="BS_FAIT",
        template_name="emails/bs_faits.html",
        subject=f"BS validés – {mois.client} – {mois.mois}/{mois.annee}",
        context={
            "mois": mois,
            "preheader": f"Les bulletins de salaire {mois.mois}/{mois.annee} ont été validés pour {mois.client}."
        },
    )


def envoyer_notifications_dsn(mois):
    envoyer_email(
        event="DSN_FAITE",
        template_name="emails/dsn_faite.html",
        subject=f"DSN validée – {mois.client} – {mois.mois}/{mois.annee}",
        context={
            "mois": mois,
            "preheader": f"La DSN {mois.mois}/{mois.annee} a été validée pour {mois.client}."
        },
    )
