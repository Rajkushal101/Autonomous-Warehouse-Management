from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.repositories.base import get_db
from app.models.entities import User
from app.api.deps import get_current_user
from app.services.inventory_service import InventoryService
from app.domain.models import WarehouseSecurityException
from app.core.config import settings

router = APIRouter(prefix="/inventory", tags=["Inventory"])

class StockAdjustmentRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    location_code: str = Field(..., min_length=1, max_length=32)
    delta: int = Field(...)
    reason: str = Field(..., min_length=5, max_length=255)

@router.get("/balances")
def get_inventory_balances(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return InventoryService.get_balances(db, current_user, settings.WAREHOUSE_ID)
    except WarehouseSecurityException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

@router.post("/adjustments")
def adjust_inventory_stock(req: StockAdjustmentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        balance = InventoryService.adjust_stock(
            db=db,
            actor=current_user,
            warehouse_id=settings.WAREHOUSE_ID,
            sku=req.sku,
            location_code=req.location_code,
            delta=req.delta,
            reason=req.reason
        )
        return {
            "status": "success",
            "sku": req.sku,
            "location": req.location_code,
            "on_hand": balance.on_hand,
            "reserved": balance.reserved,
            "available": balance.on_hand - balance.reserved
        }
    except WarehouseSecurityException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})
