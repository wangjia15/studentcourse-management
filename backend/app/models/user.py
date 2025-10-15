import enum

from sqlalchemy import Boolean, Column, Enum, String
from sqlalchemy.orm import relationship

from .base import BaseModel


class UserRole(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = Column(Boolean, default=True)
    student_id = Column(String, unique=True, index=True, nullable=True)
    teacher_id = Column(String, unique=True, index=True, nullable=True)

    # Relationships
    taught_courses = relationship("Course", back_populates="teacher")
    grades = relationship("Grade", back_populates="student")
    audit_logs = relationship("AuditLog", back_populates="user")
