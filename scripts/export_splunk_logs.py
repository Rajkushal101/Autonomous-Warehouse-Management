import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.repositories.base import SessionLocal
from app.models.entities import AuditEvent

def export_logs():
    db = SessionLocal()
    events = db.query(AuditEvent).order_by(AuditEvent.timestamp.asc()).all()

    log_lines = []
    json_records = []

    for e in events:
        rec = {
            "timestamp": e.timestamp.isoformat(),
            "event_id": str(e.id),
            "actor_id": str(e.actor_id),
            "actor_type": e.actor_type,
            "action": e.action,
            "target_entity": e.target_entity,
            "target_id": str(e.target_id) if e.target_id else None,
            "outcome": e.outcome,
            "reason_code": e.reason_code,
            "ip_address": e.ip_address,
            "metadata": json.loads(e.metadata_json) if e.metadata_json else {}
        }
        json_records.append(rec)
        log_lines.append(f"{e.timestamp.isoformat()} [SECURITY_AUDIT] actor={e.actor_id} type={e.actor_type} action={e.action} target={e.target_entity} outcome={e.outcome} reason={e.reason_code} ip={e.ip_address or '127.0.0.1'}")

    log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "warehouse_audit_events.log"))
    json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "warehouse_audit_events.json"))

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_records, f, indent=2)

    print(f"Exported {len(events)} events to:")
    print(f" - {log_path}")
    print(f" - {json_path}")
    db.close()

if __name__ == "__main__":
    export_logs()
