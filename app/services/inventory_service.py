from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.entities import Product, Location, InventoryBalance, InventoryMovement, User
from app.domain.models import Role, MovementType, WarehouseSecurityException, AuditOutcome
from app.services.policy import AccessPolicy
from app.services.audit_service import AuditService
from app.core.security import get_utc_now
import uuid

class InventoryService:
    @staticmethod
    def adjust_stock(
        db: Session,
        actor: User,
        warehouse_id: str,
        sku: str,
        location_code: str,
        delta: int,
        reason: str
    ) -> InventoryBalance:
        AccessPolicy.require_role(actor, [Role.MANAGER, Role.ADMIN], db=db, action_name="STOCK_ADJUSTMENT")

        if not reason or len(reason.strip()) < 5:
            raise WarehouseSecurityException("A valid adjustment reason (min 5 chars) is mandatory", code="INVALID_REASON", status_code=422)

        if delta == 0:
            raise WarehouseSecurityException("Stock delta cannot be zero", code="INVALID_DELTA", status_code=422)

        product = db.query(Product).filter(Product.sku == sku, Product.is_active == True).first()
        if not product:
            raise WarehouseSecurityException(f"Product with SKU '{sku}' not found", code="PRODUCT_NOT_FOUND", status_code=404)

        location = db.query(Location).filter(Location.warehouse_id == warehouse_id, Location.code == location_code).first()
        if not location:
            raise WarehouseSecurityException(f"Location '{location_code}' not found", code="LOCATION_NOT_FOUND", status_code=404)

        # Row lock balance
        balance = db.query(InventoryBalance).filter(
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.product_id == product.id,
            InventoryBalance.location_id == location.id
        ).with_for_update().first()

        if not balance:
            if delta < 0:
                raise WarehouseSecurityException("Cannot deduct stock from non-existent balance", code="INSUFFICIENT_STOCK", status_code=409)
            balance = InventoryBalance(
                warehouse_id=warehouse_id,
                product_id=product.id,
                location_id=location.id,
                on_hand=0,
                reserved=0
            )
            db.add(balance)
            db.flush()

        new_on_hand = balance.on_hand + delta
        if new_on_hand < balance.reserved:
            raise WarehouseSecurityException(
                f"Adjustment violates invariant: on_hand ({new_on_hand}) cannot fall below reserved ({balance.reserved})",
                code="INVARIANT_VIOLATION",
                status_code=409
            )
        if new_on_hand < 0:
            raise WarehouseSecurityException("On-hand stock cannot be negative", code="INVARIANT_VIOLATION", status_code=409)

        balance.on_hand = new_on_hand
        balance.version += 1

        # Append immutable movement record
        movement = InventoryMovement(
            product_id=product.id,
            from_location_id=location.id if delta < 0 else None,
            to_location_id=location.id if delta > 0 else None,
            qty=abs(delta),
            movement_type=MovementType.ADJUSTMENT.value,
            source_event_id=str(uuid.uuid4()),
            reason=reason,
            actor_id=actor.id,
            created_at=get_utc_now()
        )
        db.add(movement)

        AuditService.log_event(
            db=db,
            actor_id=actor.id,
            actor_type="USER",
            action="STOCK_ADJUSTMENT",
            target_entity="INVENTORY_BALANCE",
            target_id=balance.id,
            outcome=AuditOutcome.SUCCESS,
            reason_code="MANUAL_ADJUSTMENT_COMMITTED",
            metadata={"sku": sku, "location": location_code, "delta": delta, "reason": reason}
        )

        db.commit()
        return balance

    @staticmethod
    def get_balances(db: Session, actor: User, warehouse_id: str) -> List[dict]:
        AccessPolicy.require_role(actor, [Role.OPERATOR, Role.MANAGER, Role.ADMIN, Role.AUDITOR], db=db, action_name="VIEW_BALANCES")
        
        balances = db.query(InventoryBalance).filter(InventoryBalance.warehouse_id == warehouse_id).all()
        results = []
        for b in balances:
            results.append({
                "id": b.id,
                "sku": b.product.sku,
                "product_name": b.product.name,
                "location_code": b.location.code,
                "location_type": b.location.type,
                "on_hand": b.on_hand,
                "reserved": b.reserved,
                "available": b.on_hand - b.reserved
            })
        return results
