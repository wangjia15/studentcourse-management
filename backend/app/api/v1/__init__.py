from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, courses, grades, users,
    analytics, reports, admin, teachers, students
)

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User management endpoints
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Course management endpoints
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])

# Grade management endpoints
api_router.include_router(grades.router, prefix="/grades", tags=["grades"])

# Analytics and statistics endpoints
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# Report generation endpoints
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

# System administration endpoints
api_router.include_router(admin.router, prefix="/admin", tags=["administration"])

# Teacher-specific endpoints
api_router.include_router(teachers.router, prefix="/teachers", tags=["teachers"])

# Student-specific endpoints
api_router.include_router(students.router, prefix="/students", tags=["students"])
