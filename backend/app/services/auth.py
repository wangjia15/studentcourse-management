import hashlib
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.models.auth_log import AuthAction, AuthLog, LoginAttempt, RefreshToken
from app.models.user import User as UserModel


class AuthService:
    def __init__(self):
        pass

    def log_auth_event(
        self,
        db: Session,
        user_id: Optional[int],
        action: AuthAction,
        ip_address: str,
        user_agent: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> AuthLog:
        """Log authentication events for security monitoring."""
        auth_log = AuthLog(
            user_id=user_id,
            action=action.value,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )
        db.add(auth_log)
        db.commit()
        return auth_log

    def is_ip_locked(self, db: Session, username: str, ip_address: str) -> bool:
        """Check if IP or username is locked due to too many failed attempts."""
        # Check IP-based lock
        ip_attempt = (
            db.query(LoginAttempt)
            .filter(
                LoginAttempt.ip_address == ip_address,
                LoginAttempt.is_locked == True,
                LoginAttempt.locked_until > datetime.utcnow(),
            )
            .first()
        )

        if ip_attempt:
            return True

        # Check username-based lock
        user_attempt = (
            db.query(LoginAttempt)
            .filter(
                LoginAttempt.username == username,
                LoginAttempt.is_locked == True,
                LoginAttempt.locked_until > datetime.utcnow(),
            )
            .first()
        )

        return user_attempt is not None

    def record_failed_login(
        self, db: Session, username: str, ip_address: str
    ) -> bool:
        """Record failed login attempt and return if the account should be locked."""
        # Get or create login attempt record
        attempt = (
            db.query(LoginAttempt)
            .filter(
                LoginAttempt.username == username, LoginAttempt.ip_address == ip_address
            )
            .first()
        )

        if not attempt:
            attempt = LoginAttempt(username=username, ip_address=ip_address)
            db.add(attempt)
        else:
            # Reset attempts if the timeout period has passed
            if (
                attempt.last_attempt_at
                and datetime.utcnow() - attempt.last_attempt_at
                > timedelta(seconds=settings.LOGIN_ATTEMPT_TIMEOUT)
            ):
                attempt.attempts = 1
                attempt.is_locked = False
                attempt.locked_until = None
            else:
                attempt.attempts += 1

        attempt.last_attempt_at = datetime.utcnow()

        # Lock the account if max attempts reached
        if attempt.attempts >= settings.MAX_LOGIN_ATTEMPTS:
            attempt.is_locked = True
            attempt.locked_until = datetime.utcnow() + timedelta(
                seconds=settings.LOGIN_ATTEMPT_TIMEOUT
            )
            db.commit()
            return True

        db.commit()
        return False

    def clear_failed_attempts(self, db: Session, username: str, ip_address: str):
        """Clear failed login attempts after successful login."""
        db.query(LoginAttempt).filter(
            LoginAttempt.username == username, LoginAttempt.ip_address == ip_address
        ).delete()
        db.commit()

    def hash_refresh_token(self, token: str) -> str:
        """Hash refresh token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def create_refresh_token_record(
        self, db: Session, user_id: int, refresh_token: str
    ) -> RefreshToken:
        """Create refresh token record in database."""
        token_hash = self.hash_refresh_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token_record = RefreshToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        db.add(refresh_token_record)
        db.commit()
        db.refresh(refresh_token_record)
        return refresh_token_record

    def revoke_refresh_token(self, db: Session, token_hash: str) -> bool:
        """Revoke a refresh token."""
        token_record = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash, RefreshToken.is_revoked == False)
            .first()
        )

        if token_record:
            token_record.is_revoked = True
            db.commit()
            return True
        return False

    def validate_refresh_token(self, db: Session, refresh_token: str) -> Optional[UserModel]:
        """Validate refresh token and return user."""
        token_hash = self.hash_refresh_token(refresh_token)

        token_record = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if not token_record:
            return None

        # Update last used timestamp
        token_record.last_used_at = datetime.utcnow()
        db.commit()

        # Return the associated user
        return db.query(UserModel).filter(UserModel.id == token_record.user_id).first()

    def revoke_all_user_tokens(self, db: Session, user_id: int):
        """Revoke all refresh tokens for a user (used on logout/password change)."""
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id, RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        db.commit()

    def cleanup_expired_tokens(self, db: Session):
        """Clean up expired refresh tokens."""
        db.query(RefreshToken).filter(
            RefreshToken.expires_at < datetime.utcnow()
        ).delete()
        db.commit()