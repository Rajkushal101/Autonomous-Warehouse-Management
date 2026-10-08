from typing import List, Union
from app.domain.models import Role, WarehouseSecurityException, AuditOutcome
from app.models.entities import User
from app.services.audit_service import AuditService
from sqlalchemy.orm import Session

class AccessPolicy:
    @staticmethod
    def require_role(user: User, allowed_roles: List[Union[Role, str]], db: Session = None, action_name: str = "UNKNOWN_ACTION") -> None:
        if not user or not user.is_active:
            if db and user:
                AuditService.log_event(
                    db=db,
                    actor_id=user.id,
                    actor_type="USER",
                    action=action_name,
                    target_entity="ROLE_PERMISSION",
                    target_id=None,
                    outcome=AuditOutcome.DENIED,
                    reason_code="ACCOUNT_INACTIVE_OR_REVOKED"
                )
            raise WarehouseSecurityException("Account inactive or unauthenticated", code="UNAUTHORIZED", status_code=401)

        allowed_role_strs = [r.value if isinstance(r, Role) else r for r in allowed_roles]
        if user.role not in allowed_role_strs:
            if db:
                AuditService.log_event(
                    db=db,
                    actor_id=user.id,
                    actor_type="USER",
                    action=action_name,
                    target_entity="ROLE_PERMISSION",
                    target_id=None,
                    outcome=AuditOutcome.DENIED,
                    reason_code=f"ROLE_FORBIDDEN_HAVE_{user.role}_REQUIRE_{allowed_role_strs}"
                )
            raise WarehouseSecurityException(
                f"Access denied: User role '{user.role}' lacks permission for {action_name}",
                code="FORBIDDEN_ROLE",
                status_code=403
            )

    @staticmethod
    def require_ownership_or_manager(user: User, resource_owner_id: str, db: Session = None, action_name: str = "RESOURCE_ACCESS") -> None:
        if user.role in [Role.MANAGER.value, Role.ADMIN.value]:
            return
        if user.id != resource_owner_id:
            if db:
                AuditService.log_event(
                    db=db,
                    actor_id=user.id,
                    actor_type="USER",
                    action=action_name,
                    target_entity="OBJECT_OWNERSHIP",
                    target_id=resource_owner_id,
                    outcome=AuditOutcome.DENIED,
                    reason_code="CROSS_TENANT_IDOR_ATTEMPT"
                )
            raise WarehouseSecurityException(
                "Access denied: Resource belongs to another customer",
                code="IDOR_VIOLATION",
                status_code=404  # Return 404 to avoid disclosing existence
            )
