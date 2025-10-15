import secrets
from datetime import datetime, timedelta
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(
    data: dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, credentials_exception: Exception) -> dict[str, Any]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        token_type: str = payload.get("type")

        if username is None or user_id is None or role is None:
            raise credentials_exception

        return {
            "username": username,
            "user_id": user_id,
            "role": role,
            "token_type": token_type
        }
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


def generate_password_reset_token(email: str) -> str:
    """Generate password reset token."""
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email, "type": "password_reset"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email."""
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_type = decoded_token.get("type")
        if token_type != "password_reset":
            return None
        email = decoded_token["sub"]
        return email
    except JWTError:
        return None


def generate_secure_random_string(length: int = 32) -> str:
    """Generate a secure random string."""
    return secrets.token_urlsafe(length)


def validate_chinese_name(name: str) -> bool:
    """Validate Chinese name (contains Chinese characters)."""
    import re
    chinese_pattern = r'^[\u4e00-\u9fff]+$'
    return bool(re.match(chinese_pattern, name.strip())) if name.strip() else False


def validate_chinese_email(email: str) -> bool:
    """Validate Chinese university email format."""
    import re
    # Common Chinese university email patterns
    patterns = [
        r'^[a-zA-Z0-9._%+-]+@(edu\.cn|\.edu\.cn)$',  # Standard .edu.cn domains
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.edu\.cn$',  # Specific university domains
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.ac\.cn$',   # Academic domains
    ]

    email_lower = email.lower().strip()
    return any(re.match(pattern, email_lower) for pattern in patterns)


def validate_student_id(student_id: str) -> bool:
    """Validate Chinese university student ID format."""
    import re
    # Common patterns: 2021001001 (year + department + number)
    pattern = r'^20[0-9]{2}[0-9]{4,8}$'
    return bool(re.match(pattern, student_id))


def validate_teacher_id(teacher_id: str) -> bool:
    """Validate Chinese university teacher ID format."""
    import re
    # Teacher IDs can be various formats, usually 6-10 digits
    pattern = r'^[0-9]{6,10}$'
    return bool(re.match(pattern, teacher_id))


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password strength.
    Returns (is_valid, list_of_errors)
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if len(password) > 128:
        errors.append("Password must be less than 128 characters long")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    # Check for common patterns
    common_patterns = [
        r'123456', r'password', r'qwerty', r'admin', r'letmein',
        r'welcome', r'monkey', r'dragon', r'football', r'baseball'
    ]

    for pattern in common_patterns:
        if pattern.lower() in password.lower():
            errors.append(f"Password cannot contain common patterns like '{pattern}'")

    return len(errors) == 0, errors
