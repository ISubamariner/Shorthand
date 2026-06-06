from admin_api.models import AuditLog


def log_audit(actor, action, target_type, target_id, details=None):
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        details=details or {},
    )
