import enum

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Index, CheckConstraint
from sqlalchemy.orm import relationship

from .base import BaseModel


class CourseStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CourseType(enum.Enum):
    REQUIRED = "required"
    ELECTIVE = "elective"
    PROFESSIONAL = "professional"
    GENERAL = "general"


class Course(BaseModel):
    __tablename__ = "courses"

    # Basic Course Information
    course_code = Column(String(20), unique=True, index=True, nullable=False, comment="课程代码")
    course_name = Column(String(200), nullable=False, comment="课程名称")
    course_name_en = Column(String(200), nullable=True, comment="英文名称")
    description = Column(Text, nullable=True, comment="课程描述")
    
    # Course Classification
    course_type = Column(String(20), default=CourseType.REQUIRED.value, nullable=False, comment="课程类型")
    credits = Column(Integer, nullable=False, default=3, comment="学分")
    hours = Column(Integer, nullable=False, default=48, comment="学时")
    
    # Academic Information
    academic_year = Column(String(9), nullable=False, comment="学年 (e.g., 2024-2025)")
    semester = Column(String(20), nullable=False, comment="学期 (e.g., Fall, Spring)")
    
    # Enrollment Management
    max_students = Column(Integer, nullable=False, default=50, comment="最大学生数")
    current_enrolled = Column(Integer, default=0, nullable=False, comment="当前选课人数")
    min_students = Column(Integer, nullable=False, default=1, comment="最少开课人数")
    
    # Course Status and Management
    status = Column(String(20), default=CourseStatus.ACTIVE.value, nullable=False, comment="课程状态")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    
    # Teacher Information
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="授课教师ID")
    teaching_assistant_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="助教ID")
    
    # Course Schedule
    schedule_info = Column(Text, nullable=True, comment="上课时间地点信息")
    classroom = Column(String(100), nullable=True, comment="教室")
    exam_time = Column(String(100), nullable=True, comment="考试时间")
    exam_location = Column(String(100), nullable=True, comment="考试地点")
    
    # Grading Information
    grading_method = Column(Text, nullable=True, comment="评分方式")
    passing_score = Column(Integer, default=60, nullable=False, comment="及格分数")
    
    # Department Information
    department = Column(String(100), nullable=False, comment="开课院系")
    faculty_responsible = Column(String(100), nullable=True, comment="责任教师")

    # Relationships
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="taught_courses")
    teaching_assistant = relationship("User", foreign_keys=[teaching_assistant_id])
    grades = relationship("Grade", back_populates="course")
    enrollments = relationship("Enrollment", back_populates="course")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('credits > 0 AND credits <= 10', name='check_credits_range'),
        CheckConstraint('hours > 0 AND hours <= 200', name='check_hours_range'),
        CheckConstraint('max_students > 0 AND max_students <= 500', name='check_max_students_range'),
        CheckConstraint('passing_score >= 0 AND passing_score <= 100', name='check_passing_score_range'),
        CheckConstraint('current_enrolled >= 0 AND current_enrolled <= max_students', name='check_enrollment_range'),
        Index('idx_course_code_semester', 'course_code', 'semester'),
        Index('idx_course_department_type', 'department', 'course_type'),
        Index('idx_course_teacher_semester', 'teacher_id', 'semester'),
        Index('idx_course_status_academic', 'status', 'academic_year'),
        Index('idx_course_name', 'course_name'),
    )

    def __repr__(self):
        return f"<Course(id={self.id}, code='{self.course_code}', name='{self.course_name}')>"
