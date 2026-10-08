from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.repositories.base import get_db
from app.models.entities import User
from app.api.deps import get_current_user
from app.services.order_service import OrderService
from app.domain.models import WarehouseSecurityException
from app.core.config import settings

router = APIRouter(prefix="/orders", tags=["Orders"])

class OrderItemInput(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    quantity: int = Field(..., gt=0, le=100)

class CreateOrderRequest(BaseModel):
    items: List[OrderItemInput]

@router.post("")
def create_order(
    req: CreateOrderRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not idempotency_key:
        raise HTTPException(status_code=422, detail="Header 'Idempotency-Key' is required")

    items_dict = [{"sku": i.sku, "quantity": i.quantity} for i in req.items]
    try:
        result = OrderService.create_order_with_reservation(
            db=db,
            customer=current_user,
            warehouse_id=settings.WAREHOUSE_ID,
            items_payload=items_dict,
            idempotency_key=idempotency_key
        )
        return result
    except WarehouseSecurityException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

@router.get("")
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return OrderService.list_customer_orders(db, current_user)

@router.get("/{order_id}")
def get_order(order_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return OrderService.get_order_by_id(db, current_user, order_id)
    except WarehouseSecurityException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})
