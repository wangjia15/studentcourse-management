from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class Grade(BaseModel):
    __tablename__ = "grades"

    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    score = Column(Float, nullable=False)
    grade_letter = Column(String, nullable=True)  # A, B, C, D, F
    grade_type = Column(String, nullable=False)  # midterm, final, assignment, quiz
    max_score = Column(Float, nullable=False, default=100.0)
    weight = Column(Float, nullable=False, default=1.0)
    comments = Column(Text, nullable=True)

    # Relationships
    student = relationship("User", back_populates="grades")
    course = relationship("Course", back_populates="grades")

    # Add check constraint for score
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= max_score", name="check_score_range"),
    )
