import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import AuditEvent
from app.domain.models import AuditOutcome
from app.core.security import get_utc_now

SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "cookie", "token_digest"}

def sanitize_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    sanitized = {}
    for k, v in data.items():
        if any(s in k.lower() for s in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_metadata(v)
        else:
            sanitized[k] = v
    return sanitized

class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        actor_id: str,
        actor_type: str,
        action: str,
        target_entity: str,
        target_id: Optional[str],
        outcome: AuditOutcome,
        reason_code: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        safe_meta = sanitize_metadata(metadata or {})
        event = AuditEvent(
            timestamp=get_utc_now(),
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            target_entity=target_entity,
            target_id=target_id,
            outcome=outcome.value if isinstance(outcome, AuditOutcome) else outcome,
            reason_code=reason_code,
            ip_address=ip_address,
            metadata_json=json.dumps(safe_meta)
        )
        db.add(event)
        return event
