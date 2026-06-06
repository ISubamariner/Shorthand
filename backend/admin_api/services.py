import json
import uuid

from admin_api.models import AuditLog


class _UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def _sanitize_details(details):
    if not details:
        return {}
    return json.loads(json.dumps(details, cls=_UUIDEncoder))


def log_audit(actor, action, target_type, target_id, details=None):
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        details=_sanitize_details(details),
    )
