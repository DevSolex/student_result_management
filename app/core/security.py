import bcrypt
import hashlib
import random
import string
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings


def _normalize_password(password: str) -> bytes:
    """Pre-hash with SHA-256 to keep input within bcrypt's 72-byte limit."""
    return hashlib.sha256(password.encode()).digest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_normalize_password(password), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(_normalize_password(plain), hashed.encode())


def create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    return create_token(
        {"sub": str(user_id), "role": role, "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: int) -> str:
    return create_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def generate_invite_token() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=48))
