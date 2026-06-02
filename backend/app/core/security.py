"""
Security Module — JWT Authentication, Password Hashing, Data Encryption
Uses bcrypt directly (passlib has Python 3.13 issues).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import base64
import bcrypt

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.config import settings
from app.core.exceptions import AuthenticationException


# ── Password Hashing ─────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ── JWT Tokens ───────────────────────────────────────────────────────

def create_access_token(subject: str, extra_claims: dict[str, Any] = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as e:
        raise AuthenticationException(f"Invalid or expired token: {e}")


# ── Field-Level Encryption ────────────────────────────────────────────

def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    # Pad/truncate to exactly 32 bytes then base64-encode
    key_bytes = key.encode("utf-8")[:32].ljust(32, b"0")
    encoded = base64.urlsafe_b64encode(key_bytes)
    return Fernet(encoded)


def encrypt_field(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_field(encrypted_value: str) -> str:
    return _get_fernet().decrypt(encrypted_value.encode()).decode()
