"""
Course management and enrollment tests.
"""
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings


class TestCourseManagement:
    """Test course CRUD operations and management."""

    def test_create_course_as_teacher(self, client, auth_headers_teacher, sample_course):
        """Test creating a course as teacher."""
        response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json=sample_course,
            headers=auth_headers_teacher
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == sample_course["code"]
        assert data["name"] == sample_course["name"]
        assert data["teacher_id"] == 1  # Current teacher's ID

    def test_create_course_as_admin(self, client, auth_headers_admin, sample_course):
        """Test creating a course as admin."""
        response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json=sample_course,
            headers=auth_headers_admin
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == sample_course["code"]

    def test_create_course_as_student_unauthorized(self, client, auth_headers_student, sample_course):
        """Test that students cannot create courses."""
        response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json=sample_course,
            headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_list_courses_public(self, client):
        """Test listing courses without authentication."""
        response = client.get(f"{settings.API_V1_STR}/courses/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_courses_as_teacher(self, client, auth_headers_teacher, created_course):
        """Test listing courses as teacher."""
        response = client.get(
            f"{settings.API_V1_STR}/courses/",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_course_by_id(self, client, created_course):
        """Test getting course by ID."""
        course_id = created_course["id"]
        response = client.get(f"{settings.API_V1_STR}/courses/{course_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == course_id

    def test_get_course_by_id_not_found(self, client):
        """Test getting non-existent course."""
        response = client.get(f"{settings.API_V1_STR}/courses/99999")
        assert response.status_code == 404

    def test_update_course_as_teacher(self, client, auth_headers_teacher, created_course):
        """Test updating course as teacher."""
        course_id = created_course["id"]
        update_data = {
            "name": "更新后的课程名称",
            "description": "更新后的课程描述",
            "capacity": 150
        }

        response = client.put(
            f"{settings.API_V1_STR}/courses/{course_id}",
            json=update_data,
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["capacity"] == update_data["capacity"]

    def test_update_course_unauthorized(self, client, auth_headers_student, created_course):
        """Test that unauthorized users cannot update courses."""
        course_id = created_course["id"]
        update_data = {"name": "未授权的修改"}

        response = client.put(
            f"{settings.API_V1_STR}/courses/{course_id}",
            json=update_data,
            headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_delete_course_as_teacher(self, client, auth_headers_teacher, sample_course):
        """Test deleting course as teacher."""
        # Create course first
        create_response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json=sample_course,
            headers=auth_headers_teacher
        )
        course_id = create_response.json()["id"]

        # Delete course
        response = client.delete(
            f"{settings.API_V1_STR}/courses/{course_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_delete_course_as_admin(self, client, auth_headers_admin, created_course):
        """Test deleting course as admin."""
        course_id = created_course["id"]
        response = client.delete(
            f"{settings.API_V1_STR}/courses/{course_id}",
            headers=auth_headers_admin
        )
        assert response.status_code == 200

    def test_search_courses(self, client, created_course):
        """Test searching courses."""
        # Search by name
        response = client.get(
            f"{settings.API_V1_STR}/courses/search?name={created_course['name'][:5]}"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_filter_courses_by_department(self, client, created_course):
        """Test filtering courses by department."""
        response = client.get(
            f"{settings.API_V1_STR}/courses?department={created_course['department']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_filter_courses_by_semester(self, client, created_course):
        """Test filtering courses by semester."""
        response = client.get(
            f"{settings.API_V1_STR}/courses?semester={created_course['semester']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_my_courses_as_teacher(self, client, auth_headers_teacher, created_course):
        """Test getting teacher's own courses."""
        response = client.get(
            f"{settings.API_V1_STR}/courses/my-courses",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_my_courses_as_student(self, client, auth_headers_student):
        """Test getting student's enrolled courses."""
        response = client.get(
            f"{settings.API_V1_STR}/courses/my-courses",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCourseEnrollment:
    """Test course enrollment functionality."""

    def test_enroll_student(self, client, auth_headers_teacher, auth_headers_student, created_course):
        """Test enrolling a student in a course."""
        course_id = created_course["id"]
        enrollment_data = {
            "student_ids": [2]  # Assuming student ID is 2
        }

        response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/enroll",
            json=enrollment_data,
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_self_enroll_student(self, client, auth_headers_student, created_course):
        """Test student self-enrolling in a course."""
        course_id = created_course["id"]
        response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/enroll-self",
            headers=auth_headers_student
        )
        assert response.status_code == 200

    def test_enroll_multiple_students(self, client, auth_headers_teacher, created_course):
        """Test enrolling multiple students."""
        course_id = created_course["id"]
        enrollment_data = {
            "student_ids": [2, 3, 4]  # Multiple student IDs
        }

        response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/enroll",
            json=enrollment_data,
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_get_enrolled_students(self, client, auth_headers_teacher, created_course):
        """Test getting list of enrolled students."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/courses/{course_id}/students",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_unenroll_student(self, client, auth_headers_teacher, created_course):
        """Test unenrolling a student."""
        course_id = created_course["id"]
        student_id = 2

        response = client.delete(
            f"{settings.API_V1_STR}/courses/{course_id}/unenroll/{student_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_self_unenroll_student(self, client, auth_headers_student, created_course):
        """Test student self-unenrolling from a course."""
        course_id = created_course["id"]
        response = client.delete(
            f"{settings.API_V1_STR}/courses/{course_id}/unenroll-self",
            headers=auth_headers_student
        )
        assert response.status_code == 200

    def test_check_enrollment_capacity(self, client, auth_headers_student, created_course):
        """Test course capacity checking."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/courses/{course_id}/capacity",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert "enrolled" in data
        assert "capacity" in data
        assert "available" in data

    def test_enrollment_approval_required(self, client, auth_headers_teacher, created_course):
        """Test enrollment with approval required."""
        course_id = created_course["id"]
        # Update course to require approval
        client.put(
            f"{settings.API_V1_STR}/courses/{course_id}",
            json={"requires_approval": True},
            headers=auth_headers_teacher
        )

        # Student tries to enroll
        response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/enroll-self",
            headers=auth_headers_student
        )
        # Should be pending approval
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"

    def test_approve_enrollment(self, client, auth_headers_teacher, created_course):
        """Test approving pending enrollment."""
        course_id = created_course["id"]
        response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/approve-enrollment/1",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_reject_enrollment(self, client, auth_headers_teacher, created_course):
        """Test rejecting pending enrollment."""
        course_id = created_course["id"]
        response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/reject-enrollment/1",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_get_enrollment_history(self, client, auth_headers_student):
        """Test getting student's enrollment history."""
        response = client.get(
            f"{settings.API_V1_STR}/courses/enrollment-history",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCourseContent:
    """Test course content management."""

    def test_add_course_material(self, client, auth_headers_teacher, created_course):
        """Test adding course material."""
        course_id = created_course["id"]
        material_data = {
            "title": "课程大纲",
            "description": "本课程的教学大纲",
            "type": "document",
            "file_url": "http://example.com/syllabus.pdf"
        }

        response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/materials",
            json=material_data,
            headers=auth_headers_teacher
        )
        assert response.status_code == 201

    def test_get_course_materials(self, client, auth_headers_student, created_course):
        """Test getting course materials."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/courses/{course_id}/materials",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_course_material(self, client, auth_headers_teacher, created_course):
        """Test updating course material."""
        course_id = created_course["id"]
        # First add a material
        material_response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/materials",
            json={"title": "Test Material", "type": "document"},
            headers=auth_headers_teacher
        )
        material_id = material_response.json()["id"]

        # Update the material
        update_data = {"title": "Updated Material"}
        response = client.put(
            f"{settings.API_V1_STR}/courses/{course_id}/materials/{material_id}",
            json=update_data,
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_delete_course_material(self, client, auth_headers_teacher, created_course):
        """Test deleting course material."""
        course_id = created_course["id"]
        # First add a material
        material_response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/materials",
            json={"title": "Test Material", "type": "document"},
            headers=auth_headers_teacher
        )
        material_id = material_response.json()["id"]

        # Delete the material
        response = client.delete(
            f"{settings.API_V1_STR}/courses/{course_id}/materials/{material_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_upload_material_file(self, client, auth_headers_teacher, created_course):
        """Test uploading material file."""
        course_id = created_course["id"]
        files = {"file": ("material.pdf", b"fake_pdf_content", "application/pdf")}

        response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/materials/upload",
            files=files,
            headers=auth_headers_teacher
        )
        assert response.status_code == 201


class TestCourseAnalytics:
    """Test course analytics and statistics."""

    def test_get_course_statistics(self, client, auth_headers_teacher, created_course):
        """Test getting course statistics."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/courses/{course_id}/statistics",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_students" in data
        assert "average_grade" in data
        assert "completion_rate" in data

    def test_get_course_analytics(self, client, auth_headers_teacher, created_course):
        """Test getting course analytics."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/courses/{course_id}/analytics",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert "performance_trends" in data
        assert "engagement_metrics" in data

    def test_export_course_data(self, client, auth_headers_teacher, created_course):
        """Test exporting course data."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/courses/{course_id}/export",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_get_course_attendance(self, client, auth_headers_teacher, created_course):
        """Test getting course attendance data."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/courses/{course_id}/attendance",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)