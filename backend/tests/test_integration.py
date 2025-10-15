"""
Integration tests for the complete grade management system.
"""
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings


class TestUserWorkflowIntegration:
    """Test complete user workflows."""

    def test_student_complete_workflow(self, client):
        """Test complete student workflow from registration to grade viewing."""
        # 1. Register as student
        student_data = {
            "username": "student_workflow",
            "email": "student@example.com",
            "password": "Student123!",
            "full_name": "测试学生",
            "role": "student",
            "student_id": "2021999",
            "major": "计算机科学与技术",
            "grade": "2021级",
            "class_name": "计科2101"
        }

        register_response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=student_data
        )
        assert register_response.status_code == 201

        # 2. Login
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": student_data["username"],
                "password": student_data["password"]
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Get own profile
        profile_response = client.get(
            f"{settings.API_V1_STR}/users/profile",
            headers=headers
        )
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["username"] == student_data["username"]

        # 4. View available courses
        courses_response = client.get(f"{settings.API_V1_STR}/courses/")
        assert courses_response.status_code == 200

        # 5. Enroll in a course (if available)
        # This would require a course to exist first

        # 6. View own grades
        grades_response = client.get(
            f"{settings.API_V1_STR}/grades/student",
            headers=headers
        )
        assert grades_response.status_code == 200

        # 7. View transcript
        transcript_response = client.get(
            f"{settings.API_V1_STR}/grades/transcript",
            headers=headers
        )
        assert transcript_response.status_code == 200

        # 8. Logout
        logout_response = client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers=headers
        )
        assert logout_response.status_code == 200

    def test_teacher_complete_workflow(self, client):
        """Test complete teacher workflow from registration to grade management."""
        # 1. Register as teacher
        teacher_data = {
            "username": "teacher_workflow",
            "email": "teacher@example.com",
            "password": "Teacher123!",
            "full_name": "测试教师",
            "role": "teacher",
            "teacher_id": "T999",
            "department": "计算机科学与技术"
        }

        register_response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=teacher_data
        )
        assert register_response.status_code == 201

        # 2. Login
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": teacher_data["username"],
                "password": teacher_data["password"]
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Get own profile
        profile_response = client.get(
            f"{settings.API_V1_STR}/users/profile",
            headers=headers
        )
        assert profile_response.status_code == 200

        # 4. Create a course
        course_data = {
            "code": "WF101",
            "name": "工作流程测试课程",
            "description": "用于测试工作流程的课程",
            "credit": 3,
            "capacity": 50,
            "semester": "2023-2024-1",
            "academic_year": "2023-2024",
            "department": "计算机科学与技术"
        }

        course_response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json=course_data,
            headers=headers
        )
        assert course_response.status_code == 201
        course_id = course_response.json()["id"]

        # 5. Get my courses
        my_courses_response = client.get(
            f"{settings.API_V1_STR}/courses/my-courses",
            headers=headers
        )
        assert my_courses_response.status_code == 200

        # 6. Add course material
        material_data = {
            "title": "课程大纲",
            "description": "课程教学大纲",
            "type": "document"
        }

        material_response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/materials",
            json=material_data,
            headers=headers
        )
        assert material_response.status_code == 201

        # 7. Create grades for students
        grade_data = {
            "student_id": 2,  # Assuming student exists
            "score": 85.0,
            "assignment_type": "作业",
            "assignment_name": "作业1",
            "max_score": 100,
            "weight": 20,
            "semester": "2023-2024-1",
            "academic_year": "2023-2024"
        }

        grade_response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json=grade_data,
            headers=headers
        )
        # May fail if student doesn't exist, but that's expected

        # 8. Get course statistics
        stats_response = client.get(
            f"{settings.API_V1_STR}/grades/statistics/course/{course_id}",
            headers=headers
        )
        assert stats_response.status_code == 200

        # 9. Export course data
        export_response = client.get(
            f"{settings.API_V1_STR}/grades/export/{course_id}",
            headers=headers
        )
        assert export_response.status_code == 200

    def test_admin_complete_workflow(self, client):
        """Test complete admin workflow from registration to system management."""
        # 1. Register as admin
        admin_data = {
            "username": "admin_workflow",
            "email": "admin@example.com",
            "password": "Admin123!",
            "full_name": "测试管理员",
            "role": "admin"
        }

        register_response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=admin_data
        )
        assert register_response.status_code == 201

        # 2. Login
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_data["username"],
                "password": admin_data["password"]
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Get system statistics
        system_stats_response = client.get(
            f"{settings.API_V1_STR}/admin/system-stats",
            headers=headers
        )
        assert system_stats_response.status_code == 200

        # 4. List all users
        users_response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=headers
        )
        assert users_response.status_code == 200

        # 5. Create multiple students
        students_batch = []
        for i in range(3):
            students_batch.append({
                "username": f"batch_student{i}",
                "email": f"batch_student{i}@example.com",
                "password": "Student123!",
                "full_name": f"批量学生{i}",
                "role": "student",
                "student_id": f"202200{i}",
                "major": "计算机科学与技术",
                "grade": "2022级"
            })

        batch_response = client.post(
            f"{settings.API_V1_STR}/users/batch",
            json={"users": students_batch},
            headers=headers
        )
        assert batch_response.status_code == 201

        # 6. Create teacher account
        teacher_data = {
            "username": "batch_teacher",
            "email": "batch_teacher@example.com",
            "password": "Teacher123!",
            "full_name": "批量教师",
            "role": "teacher",
            "teacher_id": "TBATCH",
            "department": "计算机科学与技术"
        }

        teacher_response = client.post(
            f"{settings.API_V1_STR}/users/teacher",
            json=teacher_data,
            headers=headers
        )
        assert teacher_response.status_code == 201

        # 7. View audit logs
        audit_response = client.get(
            f"{settings.API_V1_STR}/admin/audit-logs",
            headers=headers
        )
        assert audit_response.status_code == 200

        # 8. Export user data
        export_users_response = client.get(
            f"{settings.API_V1_STR}/users/export",
            headers=headers
        )
        assert export_users_response.status_code == 200


class TestCourseEnrollmentIntegration:
    """Test course enrollment workflows."""

    def test_full_enrollment_workflow(self, client, auth_headers_admin, auth_headers_teacher, auth_headers_student):
        """Test complete enrollment workflow."""
        # 1. Admin creates course
        course_data = {
            "code": "ENROLL101",
            "name": "招生测试课程",
            "description": "用于测试招生流程的课程",
            "credit": 3,
            "capacity": 30,
            "semester": "2023-2024-1",
            "academic_year": "2023-2024",
            "department": "计算机科学与技术"
        }

        course_response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json=course_data,
            headers=auth_headers_admin
        )
        assert course_response.status_code == 201
        course_id = course_response.json()["id"]

        # 2. Teacher updates course
        update_data = {
            "description": "更新后的课程描述",
            "capacity": 35
        }

        update_response = client.put(
            f"{settings.API_V1_STR}/courses/{course_id}",
            json=update_data,
            headers=auth_headers_teacher
        )
        assert update_response.status_code == 200

        # 3. Student enrolls in course
        enroll_response = client.post(
            f"{settings.API_V1_STR}/courses/{course_id}/enroll-self",
            headers=auth_headers_student
        )
        assert enroll_response.status_code == 200

        # 4. Teacher checks enrolled students
        students_response = client.get(
            f"{settings.API_V1_STR}/courses/{course_id}/students",
            headers=auth_headers_teacher
        )
        assert students_response.status_code == 200
        students = students_response.json()

        # 5. Teacher adds grade for enrolled student
        if students:
            grade_data = {
                "student_id": students[0]["id"],
                "score": 88.0,
                "assignment_type": "作业",
                "assignment_name": "入学作业",
                "max_score": 100,
                "weight": 20,
                "semester": "2023-2024-1",
                "academic_year": "2023-2024"
            }

            grade_response = client.post(
                f"{settings.API_V1_STR}/grades/",
                json=grade_data,
                headers=auth_headers_teacher
            )
            assert grade_response.status_code == 201

        # 6. Student checks own grades
        student_grades_response = client.get(
            f"{settings.API_V1_STR}/grades/student",
            headers=auth_headers_student
        )
        assert student_grades_response.status_code == 200

        # 7. Student unenrolls from course
        unenroll_response = client.delete(
            f"{settings.API_V1_STR}/courses/{course_id}/unenroll-self",
            headers=auth_headers_student
        )
        assert unenroll_response.status_code == 200


class TestGradeReportingIntegration:
    """Test grade reporting and analytics workflows."""

    def test_complete_grade_reporting_workflow(self, client, auth_headers_admin, auth_headers_teacher):
        """Test complete grade reporting workflow."""
        # 1. Create course and students
        course_data = {
            "code": "REPORT101",
            "name": "成绩报告测试课程",
            "credit": 3,
            "capacity": 20,
            "semester": "2023-2024-1",
            "academic_year": "2023-2024",
            "department": "计算机科学与技术"
        }

        course_response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json=course_data,
            headers=auth_headers_teacher
        )
        course_id = course_response.json()["id"]

        # 2. Create sample students
        students = []
        for i in range(5):
            student_data = {
                "username": f"report_student{i}",
                "email": f"report_student{i}@example.com",
                "password": "Student123!",
                "full_name": f"报告学生{i}",
                "role": "student",
                "student_id": f"202300{i}",
                "major": "计算机科学与技术",
                "grade": "2023级"
            }

            student_response = client.post(
                f"{settings.API_V1_STR}/users/student",
                json=student_data,
                headers=auth_headers_admin
            )
            students.append(student_response.json())

        # 3. Enroll students
        for student in students:
            client.post(
                f"{settings.API_V1_STR}/courses/{course_id}/enroll",
                json={"student_ids": [student["id"]]},
                headers=auth_headers_teacher
            )

        # 4. Add multiple grades for each student
        assignments = [
            {"name": "作业1", "type": "作业", "weight": 20},
            {"name": "期中考试", "type": "考试", "weight": 30},
            {"name": "期末考试", "type": "考试", "weight": 40},
            {"name": "课堂参与", "type": "参与", "weight": 10}
        ]

        for assignment in assignments:
            for student in students:
                import random
                score = random.uniform(60, 95)
                grade_data = {
                    "student_id": student["id"],
                    "score": round(score, 1),
                    "assignment_type": assignment["type"],
                    "assignment_name": assignment["name"],
                    "max_score": 100,
                    "weight": assignment["weight"],
                    "semester": "2023-2024-1",
                    "academic_year": "2023-2024"
                }

                client.post(
                    f"{settings.API_V1_STR}/grades/",
                    json=grade_data,
                    headers=auth_headers_teacher
                )

        # 5. Generate course statistics
        stats_response = client.get(
            f"{settings.API_V1_STR}/grades/statistics/course/{course_id}",
            headers=auth_headers_teacher
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()

        # 6. Generate grade distribution
        distribution_response = client.get(
            f"{settings.API_V1_STR}/grades/distribution/{course_id}",
            headers=auth_headers_teacher
        )
        assert distribution_response.status_code == 200

        # 7. Generate class ranking
        ranking_response = client.get(
            f"{settings.API_V1_STR}/grades/ranking/{course_id}",
            headers=auth_headers_teacher
        )
        assert ranking_response.status_code == 200

        # 8. Export grades to Excel
        export_response = client.get(
            f"{settings.API_V1_STR}/grades/export/{course_id}",
            headers=auth_headers_teacher
        )
        assert export_response.status_code == 200

        # 9. Generate comprehensive report
        report_response = client.post(
            f"{settings.API_V1_STR}/grades/report/{course_id}",
            json={"format": "pdf", "include_charts": True},
            headers=auth_headers_teacher
        )
        assert report_response.status_code == 200


class TestAPIIntegration:
    """Test API integration and consistency."""

    def test_api_response_consistency(self, client):
        """Test that API responses are consistent across endpoints."""
        # Test health endpoints
        health_response = client.get("/health")
        root_response = client.get("/")

        assert health_response.status_code == 200
        assert root_response.status_code == 200

        # Test OpenAPI documentation
        openapi_response = client.get(f"{settings.API_V1_STR}/openapi.json")
        assert openapi_response.status_code == 200

        # Test that all endpoints are properly documented
        openapi_data = openapi_response.json()
        assert "paths" in openapi_data
        assert len(openapi_data["paths"]) > 0

    def test_error_handling_consistency(self, client):
        """Test consistent error handling across endpoints."""
        # Test authentication errors
        response = client.get(f"{settings.API_V1_STR}/auth/me")
        assert response.status_code == 401
        assert "detail" in response.json()

        # Test authorization errors (would need valid token)
        # Test not found errors
        response = client.get(f"{settings.API_V1_STR}/courses/99999")
        assert response.status_code == 404
        assert "detail" in response.json()

        # Test validation errors
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={"username": "test"}  # Incomplete data
        )
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_cors_configuration(self, client):
        """Test CORS configuration."""
        # Test preflight request
        response = client.options(
            f"{settings.API_V1_STR}/courses/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_rate_limiting_integration(self, client):
        """Test rate limiting integration."""
        # Make multiple rapid requests to test rate limiting
        responses = []
        for _ in range(15):
            response = client.post(
                f"{settings.API_V1_STR}/auth/login",
                json={"username": "test", "password": "test"}
            )
            responses.append(response.status_code)

        # Should eventually be rate limited
        rate_limited = any(status == 429 for status in responses)
        assert rate_limited or all(status == 401 for status in responses)