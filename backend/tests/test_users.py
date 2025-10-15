"""
User management and profile tests.
"""
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings


class TestUserManagement:
    """Test user CRUD operations and management."""

    def test_create_student_user(self, client, auth_headers_admin, student_user):
        """Test creating a student user."""
        response = client.post(
            f"{settings.API_V1_STR}/users/student",
            json=student_user,
            headers=auth_headers_admin
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == student_user["username"]
        assert data["role"] == "student"
        assert data["student_id"] == student_user["student_id"]
        assert "id" in data

    def test_create_teacher_user(self, client, auth_headers_admin, teacher_user):
        """Test creating a teacher user."""
        response = client.post(
            f"{settings.API_V1_STR}/users/teacher",
            json=teacher_user,
            headers=auth_headers_admin
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == teacher_user["username"]
        assert data["role"] == "teacher"
        assert data["teacher_id"] == teacher_user["teacher_id"]

    def test_create_admin_user(self, client, auth_headers_admin, admin_user):
        """Test creating an admin user."""
        response = client.post(
            f"{settings.API_V1_STR}/users/admin",
            json=admin_user,
            headers=auth_headers_admin
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == admin_user["username"]
        assert data["role"] == "admin"

    def test_list_users_as_admin(self, client, auth_headers_admin, auth_headers_teacher):
        """Test listing users as admin."""
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_users_unauthorized(self, client, auth_headers_student):
        """Test that non-admin cannot list users."""
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_get_user_by_id(self, client, auth_headers_admin, created_student):
        """Test getting user by ID."""
        user_id = created_student["id"]
        response = client.get(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id

    def test_get_user_by_id_not_found(self, client, auth_headers_admin):
        """Test getting non-existent user."""
        response = client.get(
            f"{settings.API_V1_STR}/users/99999",
            headers=auth_headers_admin
        )
        assert response.status_code == 404

    def test_update_user_profile(self, client, auth_headers_student, student_user):
        """Test updating user profile."""
        update_data = {
            "full_name": "张三丰",
            "email": "zhangsanfeng@example.com",
            "phone": "13900139000"
        }

        response = client.put(
            f"{settings.API_V1_STR}/users/profile",
            json=update_data,
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["email"] == update_data["email"]

    def test_update_user_by_admin(self, client, auth_headers_admin, created_student):
        """Test admin updating user."""
        user_id = created_student["id"]
        update_data = {
            "full_name": "李四",
            "is_active": False
        }

        response = client.put(
            f"{settings.API_V1_STR}/users/{user_id}",
            json=update_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["is_active"] == update_data["is_active"]

    def test_deactivate_user(self, client, auth_headers_admin, created_student):
        """Test deactivating a user."""
        user_id = created_student["id"]
        response = client.patch(
            f"{settings.API_V1_STR}/users/{user_id}/deactivate",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_activate_user(self, client, auth_headers_admin, created_student):
        """Test activating a user."""
        user_id = created_student["id"]

        # First deactivate
        client.patch(
            f"{settings.API_V1_STR}/users/{user_id}/deactivate",
            headers=auth_headers_admin
        )

        # Then activate
        response = client.patch(
            f"{settings.API_V1_STR}/users/{user_id}/activate",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    def test_delete_user(self, client, auth_headers_admin, student_user):
        """Test deleting a user."""
        # Create user first
        create_response = client.post(
            f"{settings.API_V1_STR}/users/student",
            json=student_user,
            headers=auth_headers_admin
        )
        user_id = create_response.json()["id"]

        # Delete user
        response = client.delete(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers=auth_headers_admin
        )
        assert response.status_code == 200

        # Verify user is deleted
        response = client.get(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers=auth_headers_admin
        )
        assert response.status_code == 404

    def test_search_users_by_name(self, client, auth_headers_admin, student_user):
        """Test searching users by name."""
        # Create user
        client.post(
            f"{settings.API_V1_STR}/users/student",
            json=student_user,
            headers=auth_headers_admin
        )

        # Search by name
        response = client.get(
            f"{settings.API_V1_STR}/users/search?name={student_user['full_name']}",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert student_user["full_name"] in [user["full_name"] for user in data]

    def test_search_users_by_student_id(self, client, auth_headers_admin, student_user):
        """Test searching users by student ID."""
        # Create user
        client.post(
            f"{settings.API_V1_STR}/users/student",
            json=student_user,
            headers=auth_headers_admin
        )

        # Search by student ID
        response = client.get(
            f"{settings.API_V1_STR}/users/search?student_id={student_user['student_id']}",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert student_user["student_id"] in [user["student_id"] for user in data]

    def test_filter_users_by_role(self, client, auth_headers_admin, student_user, teacher_user):
        """Test filtering users by role."""
        # Create users
        client.post(
            f"{settings.API_V1_STR}/users/student",
            json=student_user,
            headers=auth_headers_admin
        )
        client.post(
            f"{settings.API_V1_STR}/users/teacher",
            json=teacher_user,
            headers=auth_headers_admin
        )

        # Filter by student role
        response = client.get(
            f"{settings.API_V1_STR}/users?role=student",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert all(user["role"] == "student" for user in data)

    def test_filter_users_by_department(self, client, auth_headers_admin, teacher_user):
        """Test filtering users by department."""
        # Create teacher
        client.post(
            f"{settings.API_V1_STR}/users/teacher",
            json=teacher_user,
            headers=auth_headers_admin
        )

        # Filter by department
        response = client.get(
            f"{settings.API_V1_STR}/users?department={teacher_user['department']}",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        # Should include the created teacher

    def test_batch_create_users(self, client, auth_headers_admin):
        """Test batch creating users."""
        users = [
            {
                "username": f"student{i:03d}",
                "email": f"student{i:03d}@example.com",
                "password": "Student123!",
                "full_name": f"学生{i}",
                "role": "student",
                "student_id": f"2021{i:03d}",
                "major": "计算机科学与技术",
                "grade": "2021级"
            }
            for i in range(1, 6)
        ]

        response = client.post(
            f"{settings.API_V1_STR}/users/batch",
            json={"users": users},
            headers=auth_headers_admin
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["created_users"]) == 5

    def test_user_statistics(self, client, auth_headers_admin):
        """Test getting user statistics."""
        response = client.get(
            f"{settings.API_V1_STR}/users/stats",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "by_role" in data
        assert "by_department" in data
        assert "active_users" in data

    def test_export_users(self, client, auth_headers_admin):
        """Test exporting user data."""
        response = client.get(
            f"{settings.API_V1_STR}/users/export",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]

    def test_upload_user_avatar(self, client, auth_headers_student):
        """Test uploading user avatar."""
        # Create a dummy image file
        files = {"file": ("avatar.jpg", b"fake_image_data", "image/jpeg")}

        response = client.post(
            f"{settings.API_V1_STR}/users/avatar",
            files=files,
            headers=auth_headers_student
        )
        assert response.status_code == 200

    def test_get_user_permissions(self, client, auth_headers_student):
        """Test getting user permissions."""
        response = client.get(
            f"{settings.API_V1_STR}/users/permissions",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert isinstance(data["permissions"], list)

    def test_user_audit_log(self, client, auth_headers_admin, created_student):
        """Test user audit log."""
        user_id = created_student["id"]
        response = client.get(
            f"{settings.API_V1_STR}/users/{user_id}/audit-log",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestUserProfile:
    """Test user profile specific functionality."""

    def test_get_own_profile(self, client, auth_headers_student, student_user):
        """Test getting own profile."""
        response = client.get(
            f"{settings.API_V1_STR}/users/profile",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == student_user["username"]
        assert data["email"] == student_user["email"]

    def test_update_own_profile(self, client, auth_headers_student):
        """Test updating own profile."""
        update_data = {
            "full_name": "新姓名",
            "phone": "13800138000"
        }

        response = client.put(
            f"{settings.API_V1_STR}/users/profile",
            json=update_data,
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["phone"] == update_data["phone"]

    def test_cannot_update_sensitive_fields(self, client, auth_headers_student):
        """Test that users cannot update sensitive fields."""
        update_data = {
            "role": "admin",
            "is_active": True,
            "student_id": "new_student_id"
        }

        response = client.put(
            f"{settings.API_V1_STR}/users/profile",
            json=update_data,
            headers=auth_headers_student
        )
        # Should not allow updating sensitive fields
        assert response.status_code == 400

    def test_change_avatar(self, client, auth_headers_student):
        """Test changing user avatar."""
        files = {"avatar": ("new_avatar.jpg", b"new_image_data", "image/jpeg")}

        response = client.put(
            f"{settings.API_V1_STR}/users/avatar",
            files=files,
            headers=auth_headers_student
        )
        assert response.status_code == 200

    def test_delete_avatar(self, client, auth_headers_student):
        """Test deleting user avatar."""
        response = client.delete(
            f"{settings.API_V1_STR}/users/avatar",
            headers=auth_headers_student
        )
        assert response.status_code == 200

    def test_get_user_settings(self, client, auth_headers_student):
        """Test getting user settings."""
        response = client.get(
            f"{settings.API_V1_STR}/users/settings",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert "theme" in data
        assert "language" in data
        assert "notifications" in data

    def test_update_user_settings(self, client, auth_headers_student):
        """Test updating user settings."""
        settings_data = {
            "theme": "dark",
            "language": "zh-CN",
            "notifications": {
                "email": True,
                "push": False
            }
        }

        response = client.put(
            f"{settings.API_V1_STR}/users/settings",
            json=settings_data,
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == settings_data["theme"]
        assert data["language"] == settings_data["language"]