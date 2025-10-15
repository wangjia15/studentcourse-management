from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class Course(BaseModel):
    __tablename__ = "courses"

    course_code = Column(String, unique=True, index=True, nullable=False)
    course_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    credits = Column(Integer, nullable=False, default=3)
    semester = Column(String, nullable=False)  # e.g., "2024-Fall"
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    teacher = relationship("User", back_populates="taught_courses")
    grades = relationship("Grade", back_populates="course")
