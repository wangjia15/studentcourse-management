import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Index, CheckConstraint, Float
from sqlalchemy.orm import relationship

from .base import BaseModel


class EnrollmentStatus(enum.Enum):
    PENDING = "pending"
    ENROLLED = "enrolled"
    DROPPED = "dropped"
    COMPLETED = "completed"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"


class Enrollment(BaseModel):
    __tablename__ = "enrollments"

    # Enrollment Identification
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, comment="课程ID")
    
    # Status Management
    status = Column(String(20), default=EnrollmentStatus.PENDING.value, nullable=False, comment="选课状态")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    
    # Timestamps
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="选课时间")
    dropped_at = Column(DateTime, nullable=True, comment="退课时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    # Academic Information
    academic_year = Column(String(9), nullable=False, comment="学年")
    semester = Column(String(20), nullable=False, comment="学期")
    
    # Grade Information
    final_grade = Column(Float, nullable=True, comment="最终成绩")
    gpa_points = Column(Float, nullable=True, comment="GPA学分")
    letter_grade = Column(String(2), nullable=True, comment="等级成绩")
    is_passed = Column(Boolean, nullable=True, comment="是否通过")
    
    # Attendance Information
    attendance_rate = Column(Float, default=100.0, nullable=False, comment="出勤率")
    total_classes = Column(Integer, default=0, nullable=False, comment="总课时")
    attended_classes = Column(Integer, default=0, nullable=False, comment="出勤课时")
    
    # Enrollment Management
    enrollment_type = Column(String(20), default="regular", nullable=False, comment="选课类型")
    priority = Column(Integer, default=1, nullable=False, comment="选课优先级")
    
    # Approval Information
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审批人")
    approved_at = Column(DateTime, nullable=True, comment="审批时间")
    approval_notes = Column(Text, nullable=True, comment="审批备注")
    
    # Additional Information
    notes = Column(Text, nullable=True, comment="备注")
    drop_reason = Column(Text, nullable=True, comment="退课原因")

    # Relationships
    student = relationship("User", foreign_keys=[student_id], back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    approver = relationship("User", foreign_keys=[approved_by])

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('final_grade >= 0 AND final_grade <= 100', name='check_final_grade_range'),
        CheckConstraint('gpa_points >= 0 AND gpa_points <= 4.0', name='check_gpa_points_range'),
        CheckConstraint('attendance_rate >= 0 AND attendance_rate <= 100', name='check_attendance_rate_range'),
        CheckConstraint('priority > 0 AND priority <= 10', name='check_priority_range'),
        Index('idx_enrollment_student_course', 'student_id', 'course_id', unique=True),
        Index('idx_enrollment_student_semester', 'student_id', 'semester', 'academic_year'),
        Index('idx_enrollment_course_semester', 'course_id', 'semester', 'academic_year'),
        Index('idx_enrollment_status', 'status', 'is_active'),
        Index('idx_enrollment_enrolled_at', 'enrolled_at'),
        Index('idx_enrollment_student_status', 'student_id', 'status'),
    )

    def __repr__(self):
        return f"<Enrollment(id={self.id}, student_id={self.student_id}, course_id={self.course_id}, status='{self.status}')>"
