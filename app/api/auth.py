from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.repositories.base import get_db
from app.services.auth_service import AuthService
from app.models.entities import User
from app.api.deps import get_current_user
from app.domain.models import WarehouseSecurityException
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)

@router.post("/login")
def login(req: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip_addr = request.client.host if request.client else "127.0.0.1"
    try:
        user, token, csrf_token = AuthService.authenticate_user(
            db=db,
            username=req.username,
            password=req.password,
            ip_address=ip_addr
        )
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite="lax",
            max_age=settings.SESSION_LIFETIME_SECONDS
        )
        return {
            "status": "success",
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "token": token,
            "csrf_token": csrf_token
        }
    except WarehouseSecurityException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

@router.post("/logout")
def logout(request: Request, response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    AuthService.revoke_session(db, token, current_user.id)
    response.delete_cookie(key="session_token")
    return {"status": "logged_out"}

@router.get("/me")
def get_current_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active
    }
