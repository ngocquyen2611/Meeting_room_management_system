import uuid
from typing import Any

from sqlalchemy.orm import Session

from room_service.models import AuditLog


def log_audit(
    db: Session,
    correlation_id: str,
    action: str,
    entity_name: str,
    entity_id: str | None = None,
    user_id: uuid.UUID | None = None,
    user_email: str | None = None,
    user_role: str | None = None,
    result: str = "SUCCESS",
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """
    Helper ghi nhận nhật ký kiểm toán (FR-08) vào bảng audit_logs.
    """
    try:
        log_entry = AuditLog(
            correlation_id=correlation_id or str(uuid.uuid4()),
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            action=action,
            entity_name=entity_name,
            entity_id=entity_id,
            result=result,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as e:  # noqa: BLE001 - audit failures must not fail requests
        db.rollback()
        # Audit log không được làm sập luồng chính, nhưng nên in warning
        print(f"[WARN] Failed to write audit log: {e}")
        return None
