import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.repositories.base import get_db
from app.models.entities import User, AuditEvent
from app.api.deps import get_current_user
from app.domain.models import Role
from app.services.policy import AccessPolicy

router = APIRouter(prefix="/audit", tags=["Security Audit"])

@router.get("/events")
def list_audit_events(
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    AccessPolicy.require_role(current_user, [Role.AUDITOR, Role.ADMIN], db=db, action_name="VIEW_AUDIT_LOGS")

    query = db.query(AuditEvent)
    if action:
        query = query.filter(AuditEvent.action == action)

    events = query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()

    return [{
        "id": e.id,
        "timestamp": e.timestamp.isoformat(),
        "actor_id": e.actor_id,
        "actor_type": e.actor_type,
        "action": e.action,
        "target_entity": e.target_entity,
        "target_id": e.target_id,
        "outcome": e.outcome,
        "reason_code": e.reason_code,
        "ip_address": e.ip_address,
        "metadata": json.loads(e.metadata_json) if e.metadata_json else {}
    } for e in events]
