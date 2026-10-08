from typing import Optional
from fastapi import Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from app.repositories.base import get_db
from app.models.entities import User, Robot
from app.services.auth_service import AuthService
from app.core.security import hash_token
from app.core.config import settings

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    # 1. Try Authorization Bearer header first (explicit token overrides ambient cookie)
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()

    # 2. Fall back to session cookie
    if not token:
        token = request.cookies.get("session_token")

    if not token:
        raise HTTPException(status_code=401, detail="Authentication credentials required")

    user = AuthService.get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return user

def get_current_robot(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Robot:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Device bearer token required")

    token = authorization[7:].strip()
    token_digest = hash_token(token, secret_key=settings.DEVICE_TOKEN_PEPPER)

    robot = db.query(Robot).filter(Robot.token_digest == token_digest).first()
    if not robot:
        raise HTTPException(status_code=401, detail="Invalid robot device token")
    return robot
