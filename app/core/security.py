import hmac
import hashlib
import secrets
from datetime import datetime, timezone
import bcrypt
from app.core.config import settings

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def generate_opaque_token() -> str:
    """Generates a cryptographically secure 256-bit URL-safe token."""
    return secrets.token_urlsafe(32)

def hash_token(token: str, secret_key: str = None) -> str:
    """Creates a deterministic SHA-256 HMAC digest of an opaque token for DB storage."""
    key = (secret_key or settings.SESSION_SECRET_KEY).encode("utf-8")
    return hmac.new(key, token.encode("utf-8"), hashlib.sha256).hexdigest()

def generate_csrf_token() -> str:
    return secrets.token_hex(32)

def verify_csrf_token(provided_token: str, expected_token: str) -> bool:
    if not provided_token or not expected_token:
        return False
    return hmac.compare_digest(provided_token, expected_token)

def hash_request_payload(payload_str: str) -> str:
    """Creates a SHA-256 digest of request body for idempotency record verification."""
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

def get_utc_now() -> datetime:
    """Returns UTC datetime normalized without tzinfo to ensure universal DB driver compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
