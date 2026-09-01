from dossiers.models import AuditLog

def audit(client, user, action, metadata=None, app="paie"):
    AuditLog.objects.create(
        client=client,
        user=user,
        app=app,
        action=action,
        metadata=metadata or {}
    )
