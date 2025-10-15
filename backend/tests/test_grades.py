"""
Grade management and statistics tests.
"""
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings


class TestGradeManagement:
    """Test grade CRUD operations and management."""

    def test_create_grade(self, client, auth_headers_teacher, created_course, sample_grade):
        """Test creating a grade entry."""
        course_id = created_course["id"]
        grade_data = {
            **sample_grade,
            "student_id": 2  # Assuming student ID
        }

        response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json=grade_data,
            headers=auth_headers_teacher
        )
        assert response.status_code == 201
        data = response.json()
        assert data["score"] == grade_data["score"]
        assert data["student_id"] == grade_data["student_id"]

    def test_create_grade_unauthorized(self, client, auth_headers_student, created_course, sample_grade):
        """Test that students cannot create grades."""
        course_id = created_course["id"]
        grade_data = {
            **sample_grade,
            "student_id": 2
        }

        response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json=grade_data,
            headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_get_grades_for_course(self, client, auth_headers_teacher, created_course):
        """Test getting grades for a course."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/grades/course/{course_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_student_grades(self, client, auth_headers_student):
        """Test getting student's own grades."""
        response = client.get(
            f"{settings.API_V1_STR}/grades/student",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_grades_by_assignment(self, client, auth_headers_teacher, created_course):
        """Test getting grades by assignment type."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/grades/course/{course_id}?assignment_type=作业",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_grade(self, client, auth_headers_teacher, created_course, sample_grade):
        """Test updating a grade."""
        # First create a grade
        course_id = created_course["id"]
        create_response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json={**sample_grade, "student_id": 2},
            headers=auth_headers_teacher
        )
        grade_id = create_response.json()["id"]

        # Update the grade
        update_data = {"score": 90.0, "remarks": "Updated remarks"}
        response = client.put(
            f"{settings.API_V1_STR}/grades/{grade_id}",
            json=update_data,
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == update_data["score"]
        assert data["remarks"] == update_data["remarks"]

    def test_update_grade_unauthorized(self, client, auth_headers_student, sample_grade):
        """Test that students cannot update grades."""
        grade_id = 1
        update_data = {"score": 95.0}

        response = client.put(
            f"{settings.API_V1_STR}/grades/{grade_id}",
            json=update_data,
            headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_delete_grade(self, client, auth_headers_teacher, created_course, sample_grade):
        """Test deleting a grade."""
        # First create a grade
        course_id = created_course["id"]
        create_response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json={**sample_grade, "student_id": 2},
            headers=auth_headers_teacher
        )
        grade_id = create_response.json()["id"]

        # Delete the grade
        response = client.delete(
            f"{settings.API_V1_STR}/grades/{grade_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_batch_create_grades(self, client, auth_headers_teacher, created_course):
        """Test batch creating grades."""
        course_id = created_course["id"]
        grades_data = [
            {
                "student_id": i + 2,
                "score": 80.0 + i,
                "assignment_type": "作业",
                "assignment_name": "作业1",
                "max_score": 100,
                "weight": 20,
                "semester": "2023-2024-1",
                "academic_year": "2023-2024"
            }
            for i in range(5)
        ]

        response = client.post(
            f"{settings.API_V1_STR}/grades/batch",
            json={"grades": grades_data},
            headers=auth_headers_teacher
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["created_grades"]) == 5

    def test_batch_update_grades(self, client, auth_headers_teacher, created_course):
        """Test batch updating grades."""
        course_id = created_course["id"]
        update_data = [
            {
                "grade_id": i + 1,
                "score": 90.0 + i,
                "remarks": f"Batch update {i}"
            }
            for i in range(3)
        ]

        response = client.put(
            f"{settings.API_V1_STR}/grades/batch",
            json={"grades": update_data},
            headers=auth_headers_teacher
        )
        assert response.status_code == 200

    def test_import_grades_from_csv(self, client, auth_headers_teacher, created_course):
        """Test importing grades from CSV."""
        course_id = created_course["id"]
        csv_content = """student_id,score,assignment_type,assignment_name
2,85.0,作业,作业1
3,90.0,作业,作业1
4,78.5,作业,作业1"""

        files = {"file": ("grades.csv", csv_content.encode(), "text/csv")}
        response = client.post(
            f"{settings.API_V1_STR}/grades/import/{course_id}",
            files=files,
            headers=auth_headers_teacher
        )
        assert response.status_code == 201

    def test_export_grades_to_excel(self, client, auth_headers_teacher, created_course):
        """Test exporting grades to Excel."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/grades/export/{course_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]

    def test_validate_grade_input(self, client, auth_headers_teacher, created_course):
        """Test grade input validation."""
        course_id = created_course["id"]

        # Test invalid score (too high)
        invalid_grade = {
            "student_id": 2,
            "score": 150.0,  # Invalid: > 100
            "assignment_type": "作业",
            "assignment_name": "作业1",
            "max_score": 100,
            "weight": 20,
            "semester": "2023-2024-1",
            "academic_year": "2023-2024"
        }

        response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json=invalid_grade,
            headers=auth_headers_teacher
        )
        assert response.status_code == 422

        # Test negative score
        invalid_grade["score"] = -10.0
        response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json=invalid_grade,
            headers=auth_headers_teacher
        )
        assert response.status_code == 422


class TestGradeAnalytics:
    """Test grade analytics and statistics."""

    def test_get_course_grade_statistics(self, client, auth_headers_teacher, created_course):
        """Test getting course grade statistics."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/grades/statistics/course/{course_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert "average" in data
        assert "median" in data
        assert "std_dev" in data
        assert "distribution" in data

    def test_get_student_grade_statistics(self, client, auth_headers_student):
        """Test getting student grade statistics."""
        response = client.get(
            f"{settings.API_V1_STR}/grades/statistics/student",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert "gpa" in data
        assert "total_credits" in data
        assert "average_score" in data

    def test_get_grade_distribution(self, client, auth_headers_teacher, created_course):
        """Test getting grade distribution."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/grades/distribution/{course_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert "ranges" in data
        assert "percentages" in data

    def test_get_class_ranking(self, client, auth_headers_teacher, created_course):
        """Test getting class ranking."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/grades/ranking/{course_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_assignment_statistics(self, client, auth_headers_teacher, created_course):
        """Test getting assignment-specific statistics."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/grades/statistics/assignment/{course_id}?assignment_name=作业1",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert "average" in data
        assert "highest" in data
        assert "lowest" in data

    def test_get_grade_trends(self, client, auth_headers_teacher, created_course):
        """Test getting grade trends over time."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/grades/trends/{course_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert "trend_data" in data

    def test_get_failure_analysis(self, client, auth_headers_teacher, created_course):
        """Test getting failure analysis."""
        course_id = created_course["id"]
        response = client.get(
            f"{settings.API_V1_STR}/grades/failure-analysis/{course_id}",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert "at_risk_students" in data
        assert "failure_rate" in data

    def test_calculate_gpa(self, client, auth_headers_student):
        """Test GPA calculation."""
        response = client.get(
            f"{settings.API_V1_STR}/grades/gpa",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert "gpa" in data
        assert "scale" in data
        assert isinstance(data["gpa"], (int, float))

    def test_get_transcript(self, client, auth_headers_student):
        """Test getting student transcript."""
        response = client.get(
            f"{settings.API_V1_STR}/grades/transcript",
            headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        assert "gpa" in data
        assert "total_credits" in data

    def test_generate_grade_report(self, client, auth_headers_teacher, created_course):
        """Test generating grade report."""
        course_id = created_course["id"]
        response = client.post(
            f"{settings.API_V1_STR}/grades/report/{course_id}",
            json={"format": "pdf", "include_charts": True},
            headers=auth_headers_teacher
        )
        assert response.status_code == 200


class TestGradeValidation:
    """Test grade validation and business rules."""

    def test_grade_range_validation(self, client, auth_headers_teacher, created_course):
        """Test grade range validation."""
        course_id = created_course["id"]

        # Valid grade
        valid_grade = {
            "student_id": 2,
            "score": 85.5,
            "assignment_type": "作业",
            "assignment_name": "作业1",
            "max_score": 100,
            "weight": 20,
            "semester": "2023-2024-1",
            "academic_year": "2023-2024"
        }

        response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json=valid_grade,
            headers=auth_headers_teacher
        )
        assert response.status_code == 201

        # Invalid grade (above max)
        valid_grade["score"] = 105.0
        response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json=valid_grade,
            headers=auth_headers_teacher
        )
        assert response.status_code == 422

    def test_weight_validation(self, client, auth_headers_teacher, created_course):
        """Test grade weight validation."""
        course_id = created_course["id"]

        grade = {
            "student_id": 2,
            "score": 85.0,
            "assignment_type": "作业",
            "assignment_name": "作业1",
            "max_score": 100,
            "weight": 150,  # Invalid: weight > 100
            "semester": "2023-2024-1",
            "academic_year": "2023-2024"
        }

        response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json=grade,
            headers=auth_headers_teacher
        )
        assert response.status_code == 422

    def test_duplicate_grade_prevention(self, client, auth_headers_teacher, created_course):
        """Test preventing duplicate grade entries."""
        course_id = created_course["id"]
        grade_data = {
            "student_id": 2,
            "score": 85.0,
            "assignment_type": "作业",
            "assignment_name": "作业1",
            "max_score": 100,
            "weight": 20,
            "semester": "2023-2024-1",
            "academic_year": "2023-2024"
        }

        # Create first grade
        response1 = client.post(
            f"{settings.API_V1_STR}/grades/",
            json=grade_data,
            headers=auth_headers_teacher
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post(
            f"{settings.API_V1_STR}/grades/",
            json=grade_data,
            headers=auth_headers_teacher
        )
        assert response2.status_code == 400

    def test_grade_modification_audit(self, client, auth_headers_teacher, created_course):
        """Test grade modification audit trail."""
        course_id = created_course["id"]

        # Create grade
        create_response = client.post(
            f"{settings.API_V1_STR}/grades/",
            json={
                "student_id": 2,
                "score": 80.0,
                "assignment_type": "作业",
                "assignment_name": "作业1",
                "max_score": 100,
                "weight": 20,
                "semester": "2023-2024-1",
                "academic_year": "2023-2024"
            },
            headers=auth_headers_teacher
        )
        grade_id = create_response.json()["id"]

        # Update grade
        client.put(
            f"{settings.API_V1_STR}/grades/{grade_id}",
            json={"score": 85.0},
            headers=auth_headers_teacher
        )

        # Check audit log
        response = client.get(
            f"{settings.API_V1_STR}/grades/{grade_id}/audit-log",
            headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1