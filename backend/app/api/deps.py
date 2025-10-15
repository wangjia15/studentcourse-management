from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_token
from app.db.database import get_db
from app.models.user import UserRole, User as UserModel
from app.services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
user_service = UserService()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> UserModel:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(token, credentials_exception)
    user = user_service.get_user(db, user_id=token_data["user_id"])
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user


def get_current_active_user(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def get_current_verified_user(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    """Get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
        )
    return current_user


def require_role(required_role: UserRole):
    """Decorator to require specific user role."""
    def role_checker(
        current_user: UserModel = Depends(get_current_active_user),
    ) -> UserModel:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


def require_any_role(*required_roles: UserRole):
    """Decorator to require any of the specified roles."""
    def role_checker(
        current_user: UserModel = Depends(get_current_active_user),
    ) -> UserModel:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


def require_admin(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    """Require admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_teacher_or_admin(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    """Require teacher or admin role."""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin access required",
        )
    return current_user


def require_student(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    """Require student role."""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return current_user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[UserModel]:
    """Get current user if token is provided, otherwise return None."""
    if not token:
        return None

    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        token_data = verify_token(token, credentials_exception)
        user = user_service.get_user(db, user_id=token_data["user_id"])

        if user and user.is_active:
            return user
    except Exception:
        pass

    return None


def get_client_info(request: Request) -> dict:
    """Get client information from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    else:
        ip_address = request.client.host

    user_agent = request.headers.get("User-Agent", "")

    return {
        "ip_address": ip_address,
        "user_agent": user_agent,
        "method": request.method,
        "url": str(request.url),
    }


class RateLimiter:
    """Simple in-memory rate limiter."""
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key."""
        import time

        now = int(time.time())
        window_start = now - self.window_seconds

        # Clean old requests
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key] if req_time > window_start
            ]
        else:
            self.requests[key] = []

        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True

        return False


# Rate limiters for different endpoints
login_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)  # 5 attempts per 5 minutes
password_reset_rate_limiter = RateLimiter(max_requests=3, window_seconds=3600)  # 3 attempts per hour
registration_rate_limiter = RateLimiter(max_requests=3, window_seconds=3600)  # 3 registrations per hour


def rate_login_requests(request: Request):
    """Rate limit login requests by IP address."""
    client_info = get_client_info(request)
    ip_address = client_info["ip_address"]

    if not login_rate_limiter.is_allowed(ip_address):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )


def rate_password_reset_requests(request: Request):
    """Rate limit password reset requests by IP address."""
    client_info = get_client_info(request)
    ip_address = client_info["ip_address"]

    if not password_reset_rate_limiter.is_allowed(ip_address):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset attempts. Please try again later.",
        )


def rate_registration_requests(request: Request):
    """Rate limit registration requests by IP address."""
    client_info = get_client_info(request)
    ip_address = client_info["ip_address"]

    if not registration_rate_limiter.is_allowed(ip_address):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later.",
        )