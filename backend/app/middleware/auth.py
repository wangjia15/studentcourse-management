import time
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.security import verify_token
from app.services.auth import AuthService
from app.services.permissions import Permission, PermissionService
from app.db.database import SessionLocal


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically handle JWT authentication."""

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/",
            f"/api/v1/auth/login",
            f"/api/v1/auth/register",
            f"/api/v1/auth/password-reset",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/static",
        ]
        self.auth_service = AuthService()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Get token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
            )

        token = authorization.split(" ")[1]

        try:
            # Verify token
            token_data = verify_token(
                token,
                HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                ),
            )

            # Get user from database
            db = SessionLocal()
            try:
                from app.services.user import UserService
                user_service = UserService()
                user = user_service.get_user(db, user_id=token_data["user_id"])

                if not user or not user.is_active:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "User not found or inactive"},
                    )

                # Add user info to request state
                request.state.user = user
                request.state.token_data = token_data

                return await call_next(request)

            finally:
                db.close()

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Authentication failed: {str(e)}"},
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API requests and responses."""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Log request
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        method = request.method
        path = request.url.path

        print(f"Request: {method} {path} from {client_ip}")

        # Process request
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        status_code = response.status_code

        print(f"Response: {status_code} in {process_time:.4f}s")

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window

        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] if req_time > window_start
            ]
        else:
            self.requests[client_ip] = []

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host


def require_permission(permission: Permission):
    """Decorator to require specific permission for an endpoint."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Get user from request state (set by authentication middleware)
            if not hasattr(request.state, 'user'):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authentication required"},
                )

            user = request.state.user

            # Check permission
            if not PermissionService.check_permission(user.role, permission):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": f"Permission '{permission.value}' required"},
                )

            return await func(request, *args, **kwargs)

        return wrapper
    return decorator


def require_role(role_name: str):
    """Decorator to require specific role for an endpoint."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Get user from request state
            if not hasattr(request.state, 'user'):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authentication required"},
                )

            user = request.state.user

            if user.role.value != role_name:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": f"Role '{role_name}' required"},
                )

            return await func(request, *args, **kwargs)

        return wrapper
    return decorator