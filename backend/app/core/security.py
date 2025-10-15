from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(data: dict[str, str], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, credentials_exception: Exception) -> str:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError as err:
        raise credentials_exception from err


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    # Ensure password is bytes and not longer than 72 bytes
    if isinstance(password, str):
        password_bytes = password.encode("utf-8")
    else:
        password_bytes = password
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        # Ensure both are bytes and truncate if necessary
        if isinstance(plain_password, str):
            plain_password_bytes = plain_password.encode("utf-8")
        else:
            plain_password_bytes = plain_password
        if isinstance(hashed_password, str):
            hashed_password_bytes = hashed_password.encode("utf-8")
        else:
            hashed_password_bytes = hashed_password
        if len(plain_password_bytes) > 72:
            plain_password_bytes = plain_password_bytes[:72]
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except Exception:
        return False
