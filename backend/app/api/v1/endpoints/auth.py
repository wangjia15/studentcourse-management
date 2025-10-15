from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
    verify_token,
)
from app.db.database import get_db
from app.models.auth_log import AuthAction
from app.models.user import UserRole
from app.schemas.token import (
    ChangePassword,
    PasswordReset,
    PasswordResetConfirm,
    Token,
    TokenRefresh,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
user_service = UserService()
auth_service = AuthService()


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def get_user_agent(request: Request) -> str:
    """Get user agent from request."""
    return request.headers.get("User-Agent", "")


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate user and return access/refresh tokens."""
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Check if IP or username is locked
    if auth_service.is_ip_locked(db, form_data.username, ip_address):
        auth_service.log_auth_event(
            db,
            None,
            AuthAction.LOGIN_FAILED,
            ip_address,
            user_agent,
            False,
            "Account locked due to too many failed attempts",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    # Authenticate user
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Record failed login attempt
        is_locked = auth_service.record_failed_login(db, form_data.username, ip_address)

        auth_service.log_auth_event(
            db,
            None,
            AuthAction.LOGIN_FAILED,
            ip_address,
            user_agent,
            False,
            "Invalid credentials" if not is_locked else "Account locked",
        )

        error_msg = (
            "Too many failed login attempts. Please try again later."
            if is_locked
            else "Incorrect username or password"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        auth_service.log_auth_event(
            db,
            user.id,
            AuthAction.LOGIN_FAILED,
            ip_address,
            user_agent,
            False,
            "Account is inactive",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Clear failed attempts on successful login
    auth_service.clear_failed_attempts(db, form_data.username, ip_address)

    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
        },
        expires_delta=access_token_expires,
    )

    refresh_token = create_refresh_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
        },
        expires_delta=refresh_token_expires,
    )

    # Store refresh token in database
    auth_service.create_refresh_token_record(db, user.id, refresh_token)

    # Update user's last login time
    user.last_login_at = db.execute(
        "SELECT datetime('now')"
    ).scalar()
    db.commit()

    # Log successful login
    auth_service.log_auth_event(
        db, user.id, AuthAction.LOGIN, ip_address, user_agent, True
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token."""
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Validate refresh token and get user
    user = auth_service.validate_refresh_token(db, token_data.refresh_token)
    if not user:
        auth_service.log_auth_event(
            db,
            None,
            AuthAction.TOKEN_REFRESH,
            ip_address,
            user_agent,
            False,
            "Invalid or expired refresh token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
        },
        expires_delta=access_token_expires,
    )

    # Log token refresh
    auth_service.log_auth_event(
        db, user.id, AuthAction.TOKEN_REFRESH, ip_address, user_agent, True
    )

    return {
        "access_token": access_token,
        "refresh_token": token_data.refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Logout user and revoke refresh token."""
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    try:
        # Get user from token
        token_data = verify_token(
            token,
            HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ),
        )
        user = user_service.get_user(db, user_id=token_data["user_id"])

        if user:
            # Revoke all user's refresh tokens
            auth_service.revoke_all_user_tokens(db, user.id)

            # Log logout
            auth_service.log_auth_event(
                db, user.id, AuthAction.LOGOUT, ip_address, user_agent, True
            )

    except Exception:
        pass  # Still return success for logout

    return {"message": "Successfully logged out"}


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register a new user."""
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Check if user already exists
    existing_user = user_service.get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    existing_username = user_service.get_user_by_username(db, username=user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Validate password strength
    is_valid, errors = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "errors": errors},
        )

    # Validate Chinese university specific fields
    if user_data.role == UserRole.STUDENT and not user_data.student_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID is required for student role",
        )

    if user_data.role == UserRole.TEACHER and not user_data.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher ID is required for teacher role",
        )

    # Create user
    user = user_service.create_user(db, user_data)

    # Log registration
    auth_service.log_auth_event(
        db,
        user.id,
        AuthAction.LOGIN,  # Register as a type of login event
        ip_address,
        user_agent,
        True,
    )

    return user


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Get current user information."""
    from fastapi import HTTPException, status

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(token, credentials_exception)
    user = user_service.get_user(db, user_id=token_data["user_id"])
    if user is None:
        raise credentials_exception

    return user


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Change user password."""
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(token, credentials_exception)
    user = user_service.get_user(db, user_id=token_data["user_id"])
    if user is None:
        raise credentials_exception

    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        auth_service.log_auth_event(
            db,
            user.id,
            AuthAction.PASSWORD_CHANGE,
            ip_address,
            user_agent,
            False,
            "Invalid current password",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password",
        )

    # Validate new password strength
    is_valid, errors = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "errors": errors},
        )

    # Update password
    new_hashed_password = get_password_hash(password_data.new_password)
    user.hashed_password = new_hashed_password
    db.commit()

    # Revoke all refresh tokens (force re-login on all devices)
    auth_service.revoke_all_user_tokens(db, user.id)

    # Log password change
    auth_service.log_auth_event(
        db, user.id, AuthAction.PASSWORD_CHANGE, ip_address, user_agent, True
    )

    return {"message": "Password changed successfully"}


@router.post("/password-reset")
async def request_password_reset(
    password_reset: PasswordReset,
    request: Request,
    db: Session = Depends(get_db),
):
    """Request password reset link."""
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    user = user_service.get_user_by_email(db, email=password_reset.email)
    if not user:
        # Always return success to prevent email enumeration
        return {"message": "If the email exists, a reset link has been sent"}

    # Generate password reset token (implementation would include email sending)
    # For now, we'll just log the request
    auth_service.log_auth_event(
        db, user.id, AuthAction.PASSWORD_RESET, ip_address, user_agent, True
    )

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    password_reset_confirm: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db),
):
    """Confirm password reset with token."""
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    from app.core.security import verify_password_reset_token

    email = verify_password_reset_token(password_reset_confirm.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = user_service.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate new password strength
    is_valid, errors = validate_password_strength(password_reset_confirm.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "errors": errors},
        )

    # Update password
    new_hashed_password = get_password_hash(password_reset_confirm.new_password)
    user.hashed_password = new_hashed_password
    db.commit()

    # Revoke all refresh tokens
    auth_service.revoke_all_user_tokens(db, user.id)

    # Log password reset
    auth_service.log_auth_event(
        db, user.id, AuthAction.PASSWORD_RESET, ip_address, user_agent, True
    )

    return {"message": "Password reset successfully"}
