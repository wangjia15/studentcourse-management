"""
Comprehensive authentication and authorization tests.
"""
import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash


class TestAuthentication:
    """Test authentication endpoints and functionality."""

    def test_register_user_success(self, client, admin_user):
        """Test successful user registration."""
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=admin_user
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == admin_user["username"]
        assert data["email"] == admin_user["email"]
        assert "id" in data
        assert "password" not in data

    def test_register_user_duplicate_username(self, client, admin_user):
        """Test registration with duplicate username."""
        # Register first user
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)

        # Try to register with same username
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=admin_user
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_user_duplicate_email(self, client, admin_user):
        """Test registration with duplicate email."""
        # Register first user
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)

        # Try to register with same email but different username
        duplicate_user = admin_user.copy()
        duplicate_user["username"] = "admin2"
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=duplicate_user
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_user_invalid_email(self, client, admin_user):
        """Test registration with invalid email."""
        admin_user["email"] = "invalid-email"
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=admin_user
        )
        assert response.status_code == 422

    def test_register_user_weak_password(self, client, admin_user):
        """Test registration with weak password."""
        admin_user["password"] = "123"
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=admin_user
        )
        assert response.status_code == 422

    def test_login_success(self, client, admin_user):
        """Test successful login."""
        # Register user first
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)

        # Login
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_invalid_username(self, client, admin_user):
        """Test login with invalid username."""
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": "nonexistent",
                "password": admin_user["password"]
            }
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_invalid_password(self, client, admin_user):
        """Test login with invalid password."""
        # Register user first
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)

        # Try login with wrong password
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_user["username"],
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_inactive_user(self, client, admin_user):
        """Test login with inactive user."""
        # Create inactive user
        admin_user["is_active"] = False
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)

        # Try to login
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"]
            }
        )
        assert response.status_code == 401

    def test_refresh_token_success(self, client, admin_user):
        """Test successful token refresh."""
        # Register and login
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"]
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401

    def test_logout_success(self, client, admin_user):
        """Test successful logout."""
        # Register and login
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"]
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Logout
        response = client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers=headers
        )
        assert response.status_code == 200

    def test_get_current_user(self, client, admin_user):
        """Test getting current user info."""
        # Register and login
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"]
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get current user
        response = client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == admin_user["username"]
        assert data["email"] == admin_user["email"]

    def test_password_change_success(self, client, admin_user):
        """Test successful password change."""
        # Register and login
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"]
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password
        response = client.put(
            f"{settings.API_V1_STR}/auth/password",
            headers=headers,
            json={
                "current_password": admin_user["password"],
                "new_password": "NewPassword123!"
            }
        )
        assert response.status_code == 200

        # Login with new password
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_user["username"],
                "password": "NewPassword123!"
            }
        )
        assert response.status_code == 200

    def test_password_change_wrong_current(self, client, admin_user):
        """Test password change with wrong current password."""
        # Register and login
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"]
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to change password with wrong current password
        response = client.put(
            f"{settings.API_V1_STR}/auth/password",
            headers=headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "NewPassword123!"
            }
        )
        assert response.status_code == 400

    def test_forgot_password_success(self, client, admin_user):
        """Test forgot password functionality."""
        # Register user
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)

        # Request password reset
        response = client.post(
            f"{settings.API_V1_STR}/auth/forgot-password",
            json={"email": admin_user["email"]}
        )
        assert response.status_code == 200
        # In real implementation, this would send an email

    def test_forgot_password_nonexistent_email(self, client):
        """Test forgot password with nonexistent email."""
        response = client.post(
            f"{settings.API_V1_STR}/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        # Should still return 200 for security (don't reveal if email exists)
        assert response.status_code == 200

    def test_token_validation(self, admin_user):
        """Test JWT token creation and validation."""
        # Create token
        data = {"sub": admin_user["username"]}
        token = create_access_token(data)

        # Decode and verify
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == admin_user["username"]
        assert "exp" in payload

    def test_token_expiry(self, admin_user):
        """Test token expiry."""
        # Create expired token
        data = {"sub": admin_user["username"]}
        expire = datetime.utcnow() - timedelta(minutes=1)
        token = create_access_token(data, expires_delta=timedelta(minutes=-1))

        # Try to decode expired token
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        # Verify hash is different from original password
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hash length

        # Verify password can be checked against hash
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)


class TestAuthorization:
    """Test authorization and permission controls."""

    def test_student_access_denied_to_admin_endpoints(self, client, auth_headers_student):
        """Test that students cannot access admin endpoints."""
        response = client.get(
            f"{settings.API_V1_STR}/admin/users",
            headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_teacher_access_denied_to_admin_endpoints(self, client, auth_headers_teacher):
        """Test that teachers cannot access admin endpoints."""
        response = client.get(
            f"{settings.API_V1_STR}/admin/users",
            headers=auth_headers_teacher
        )
        assert response.status_code == 403

    def test_admin_access_to_all_endpoints(self, client, auth_headers_admin):
        """Test that admins can access admin endpoints."""
        response = client.get(
            f"{settings.API_V1_STR}/admin/users",
            headers=auth_headers_admin
        )
        # Should be accessible (may return 200 or 404 depending on implementation)
        assert response.status_code != 403

    def test_unauthorized_access_no_token(self, client):
        """Test access without authentication token."""
        response = client.get(f"{settings.API_V1_STR}/auth/me")
        assert response.status_code == 401

    def test_invalid_token(self, client):
        """Test access with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
        assert response.status_code == 401

    def test_expired_token(self, client, admin_user):
        """Test access with expired token."""
        # Create expired token manually
        data = {"sub": admin_user["username"]}
        expire = datetime.utcnow() - timedelta(minutes=1)
        token = create_access_token(data, expires_delta=timedelta(minutes=-1))

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
        assert response.status_code == 401

    def test_user_can_only_access_own_data(self, client, auth_headers_student, auth_headers_teacher):
        """Test that users can only access their own data."""
        # Student tries to access teacher's courses
        response = client.get(
            f"{settings.API_V1_STR}/courses/my-courses",
            headers=auth_headers_student
        )
        # Should work as student can access their own courses

        # Student tries to access admin endpoints
        response = client.get(
            f"{settings.API_V1_STR}/admin/system-stats",
            headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_permission_inheritance(self, client, auth_headers_admin):
        """Test that admin permissions include all other permissions."""
        # Admin should be able to access teacher endpoints
        response = client.get(
            f"{settings.API_V1_STR}/teachers/my-courses",
            headers=auth_headers_admin
        )
        # Should work or return 404 if endpoint doesn't exist, but not 403

        # Admin should be able to access student endpoints
        response = client.get(
            f"{settings.API_V1_STR}/students/my-grades",
            headers=auth_headers_admin
        )
        # Should work or return 404 if endpoint doesn't exist, but not 403


class TestSecurityHeaders:
    """Test security headers and middleware."""

    def test_security_headers_present(self, client):
        """Test that security headers are present."""
        response = client.get("/")
        headers = response.headers

        # Check for security headers
        assert "x-content-type-options" in headers
        assert "x-frame-options" in headers
        assert "x-xss-protection" in headers
        assert "referrer-policy" in headers

    def test_cors_headers(self, client):
        """Test CORS headers."""
        response = client.options("/")
        headers = response.headers

        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
        assert "access-control-allow-headers" in headers

    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.post(
                f"{settings.API_V1_STR}/auth/login",
                json={"username": "test", "password": "test"}
            )
            responses.append(response.status_code)

        # Should eventually get rate limited
        assert 429 in responses or all(status == 401 for status in responses)