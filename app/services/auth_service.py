from datetime import timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.entities import User, Session as UserSession
from app.domain.models import Role, WarehouseSecurityException, AuditOutcome
from app.core.security import (
    verify_password, hash_password, generate_opaque_token, 
    hash_token, generate_csrf_token, get_utc_now
)
from app.core.config import settings
from app.services.audit_service import AuditService

# In-memory brute force tracker: {ip_or_user: [(timestamp)]}
failed_attempts = {}

class AuthService:
    @staticmethod
    def check_rate_limit(key: str) -> None:
        now = get_utc_now()
        window = timedelta(minutes=5)
        attempts = failed_attempts.get(key, [])
        # Filter within window
        attempts = [t for t in attempts if now - t < window]
        failed_attempts[key] = attempts
        if len(attempts) >= 5:
            raise WarehouseSecurityException(
                "Too many failed login attempts. Account temporarily locked for 5 minutes.",
                code="RATE_LIMITED",
                status_code=429
            )

    @staticmethod
    def record_failed_attempt(key: str) -> None:
        now = get_utc_now()
        attempts = failed_attempts.get(key, [])
        attempts.append(now)
        failed_attempts[key] = attempts

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str, ip_address: Optional[str] = None) -> Tuple[User, str, str]:
        rate_key = f"{ip_address}:{username}"
        AuthService.check_rate_limit(rate_key)

        user = db.query(User).filter(User.username == username).first()
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            AuthService.record_failed_attempt(rate_key)
            if user:
                AuditService.log_event(
                    db=db,
                    actor_id=user.id,
                    actor_type="USER",
                    action="LOGIN",
                    target_entity="USER",
                    target_id=user.id,
                    outcome=AuditOutcome.DENIED,
                    reason_code="INVALID_CREDENTIALS",
                    ip_address=ip_address
                )
                db.commit()
            raise WarehouseSecurityException("Invalid username or password", code="INVALID_CREDENTIALS", status_code=401)

        # Successful authentication: clear failure count
        failed_attempts.pop(rate_key, None)

        # Create opaque session
        token = generate_opaque_token()
        token_digest = hash_token(token)
        csrf_token = generate_csrf_token()
        expires_at = get_utc_now() + timedelta(seconds=settings.SESSION_LIFETIME_SECONDS)

        session_record = UserSession(
            user_id=user.id,
            token_digest=token_digest,
            csrf_token=csrf_token,
            expires_at=expires_at
        )
        db.add(session_record)
        AuditService.log_event(
            db=db,
            actor_id=user.id,
            actor_type="USER",
            action="LOGIN",
            target_entity="USER",
            target_id=user.id,
            outcome=AuditOutcome.SUCCESS,
            reason_code="LOGIN_SUCCESSFUL",
            ip_address=ip_address
        )
        db.commit()
        return user, token, csrf_token

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[User]:
        if not token:
            return None
        token_digest = hash_token(token)
        session_record = db.query(UserSession).filter(
            UserSession.token_digest == token_digest,
            UserSession.revoked_at.is_(None)
        ).first()

        if not session_record:
            return None

        # Check expiration
        now = get_utc_now()
        exp = session_record.expires_at
        if exp.tzinfo is not None:
            exp = exp.replace(tzinfo=None)
        if exp < now:
            return None

        user = db.query(User).filter(User.id == session_record.user_id).first()
        if not user or not user.is_active:
            return None
        return user

    @staticmethod
    def revoke_session(db: Session, token: str, actor_id: str) -> bool:
        if not token:
            return False
        token_digest = hash_token(token)
        session_record = db.query(UserSession).filter(UserSession.token_digest == token_digest).first()
        if session_record:
            session_record.revoked_at = get_utc_now()
            AuditService.log_event(
                db=db,
                actor_id=actor_id,
                actor_type="USER",
                action="LOGOUT",
                target_entity="SESSION",
                target_id=session_record.id,
                outcome=AuditOutcome.SUCCESS,
                reason_code="SESSION_REVOKED"
            )
            db.commit()
            return True
        return False
