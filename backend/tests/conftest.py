"""
Base test configuration and fixtures for the grade management system.
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.db.database import get_db, Base
from app.core.config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user():
    """Create admin user data for testing."""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "Admin123!",
        "full_name": "管理员",
        "role": "admin",
        "is_active": True
    }


@pytest.fixture
def teacher_user():
    """Create teacher user data for testing."""
    return {
        "username": "teacher001",
        "email": "teacher001@example.com",
        "password": "Teacher123!",
        "full_name": "张老师",
        "role": "teacher",
        "is_active": True,
        "teacher_id": "T001",
        "department": "计算机科学与技术"
    }


@pytest.fixture
def student_user():
    """Create student user data for testing."""
    return {
        "username": "student001",
        "email": "student001@example.com",
        "password": "Student123!",
        "full_name": "张三",
        "role": "student",
        "is_active": True,
        "student_id": "2021001",
        "major": "计算机科学与技术",
        "grade": "2021级",
        "class_name": "计科2101"
    }


@pytest.fixture
def sample_course():
    """Create sample course data for testing."""
    return {
        "code": "CS101",
        "name": "计算机科学导论",
        "description": "计算机科学基础课程",
        "credit": 3,
        "capacity": 100,
        "semester": "2023-2024-1",
        "academic_year": "2023-2024",
        "department": "计算机科学与技术",
        "teacher_id": 1
    }


@pytest.fixture
def sample_grade():
    """Create sample grade data for testing."""
    return {
        "score": 85.5,
        "assignment_type": "作业",
        "assignment_name": "作业1",
        "max_score": 100,
        "weight": 20,
        "semester": "2023-2024-1",
        "academic_year": "2023-2024",
        "remarks": "表现良好"
    }


@pytest.fixture
def auth_headers_admin(client, admin_user):
    """Get authentication headers for admin user."""
    # Register admin user
    client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)

    # Login and get token
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "username": admin_user["username"],
            "password": admin_user["password"]
        }
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_teacher(client, teacher_user):
    """Get authentication headers for teacher user."""
    # Register teacher user
    client.post(f"{settings.API_V1_STR}/auth/register", json=teacher_user)

    # Login and get token
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "username": teacher_user["username"],
            "password": teacher_user["password"]
        }
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_student(client, student_user):
    """Get authentication headers for student user."""
    # Register student user
    client.post(f"{settings.API_V1_STR}/auth/register", json=student_user)

    # Login and get token
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "username": student_user["username"],
            "password": student_user["password"]
        }
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def created_course(client, auth_headers_teacher, sample_course):
    """Create a course for testing."""
    response = client.post(
        f"{settings.API_V1_STR}/courses/",
        json=sample_course,
        headers=auth_headers_teacher
    )
    return response.json()


@pytest.fixture
def created_student(client, auth_headers_admin, student_user):
    """Create a student user for testing."""
    response = client.post(
        f"{settings.API_V1_STR}/users/student",
        json=student_user,
        headers=auth_headers_admin
    )
    return response.json()


# Test utilities
def assert_valid_response(response, expected_status=200):
    """Assert that response has valid structure and status."""
    assert response.status_code == expected_status

    if expected_status == 200:
        data = response.json()
        assert isinstance(data, dict) or isinstance(data, list)

        if isinstance(data, dict) and "message" in data:
            assert isinstance(data["message"], str)


def assert_error_response(response, expected_status, expected_message=None):
    """Assert that response has proper error structure."""
    assert response.status_code == expected_status
    data = response.json()
    assert "detail" in data

    if expected_message:
        assert expected_message.lower() in data["detail"].lower()


def create_test_user(client, user_data):
    """Helper to create a test user."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=user_data
    )
    return response.json() if response.status_code == 200 else None


def login_user(client, username, password):
    """Helper to login a user and get token."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def get_auth_headers(token):
    """Helper to create auth headers."""
    return {"Authorization": f"Bearer {token}"}


class TestDataGenerator:
    """Generate test data for various scenarios."""

    @staticmethod
    def create_batch_users(count=10, role="student"):
        """Create batch of test users."""
        users = []
        for i in range(count):
            users.append({
                "username": f"{role}{i:03d}",
                "email": f"{role}{i:03d}@example.com",
                "password": f"{role.capitalize()}123!",
                "full_name": f"{role.capitalize()} {i+1}",
                "role": role,
                "is_active": True,
                **(
                    {
                        "student_id": f"2021{i:03d}",
                        "major": "计算机科学与技术",
                        "grade": "2021级",
                        "class_name": f"计科21{i%3+1}1"
                    } if role == "student" else
                    {
                        "teacher_id": f"T{i:03d}",
                        "department": "计算机科学与技术"
                    } if role == "teacher" else {}
                )
            })
        return users

    @staticmethod
    def create_batch_courses(count=5):
        """Create batch of test courses."""
        courses = []
        departments = ["计算机科学与技术", "软件工程", "数据科学", "人工智能", "网络安全"]

        for i in range(count):
            courses.append({
                "code": f"CS{i+100:03d}",
                "name": f"计算机课程{i+1}",
                "description": f"这是计算机课程{i+1}的描述",
                "credit": (i % 4) + 1,
                "capacity": 50 + (i * 10),
                "semester": "2023-2024-1",
                "academic_year": "2023-2024",
                "department": departments[i % len(departments)],
                "teacher_id": 1
            })
        return courses

    @staticmethod
    def create_grade_distribution(student_count=30):
        """Create realistic grade distribution."""
        import random

        grades = []
        for i in range(student_count):
            # Create realistic grade distribution
            base_score = random.normalvariate(75, 15)
            score = max(0, min(100, round(base_score, 1)))

            grades.append({
                "student_id": i + 1,
                "score": score,
                "assignment_type": random.choice(["作业", "考试", "实验", "项目"]),
                "assignment_name": f"作业{random.randint(1, 5)}",
                "max_score": 100,
                "weight": random.choice([10, 15, 20, 25, 30]),
                "semester": "2023-2024-1",
                "academic_year": "2023-2024"
            })
        return grades