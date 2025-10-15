import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Float, Integer, String, Text, Index, CheckConstraint
from sqlalchemy.orm import relationship

from .base import BaseModel


class GradeType(enum.Enum):
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    MIDTERM = "midterm"
    FINAL = "final"
    PROJECT = "project"
    PARTICIPATION = "participation"
    LAB = "lab"
    OTHER = "other"


class GradeStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class Grade(BaseModel):
    __tablename__ = "grades"

    # Grade Identification
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, comment="课程ID")
    
    # Grade Information
    score = Column(Float, nullable=False, comment="得分")
    max_score = Column(Float, nullable=False, default=100.0, comment="满分")
    percentage = Column(Float, nullable=True, comment="百分比分数")
    
    # Chinese University Grade System
    letter_grade = Column(String(2), nullable=True, comment="等级成绩")
    gpa_points = Column(Float, nullable=True, comment="GPA学分")
    grade_points = Column(Float, nullable=True, comment="绩点")
    
    # Grade Classification
    grade_type = Column(String(20), nullable=False, comment="成绩类型")
    weight = Column(Float, nullable=False, default=1.0, comment="权重")
    
    # Academic Information
    academic_year = Column(String(9), nullable=False, comment="学年")
    semester = Column(String(20), nullable=False, comment="学期")
    
    # Status Management
    status = Column(String(20), default=GradeStatus.DRAFT.value, nullable=False, comment="成绩状态")
    is_final = Column(Boolean, default=False, nullable=False, comment="是否最终成绩")
    is_published = Column(Boolean, default=False, nullable=False, comment="是否已发布")
    
    # Submission Information
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="提交人ID")
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="提交时间")
    
    # Approval Information
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审批人ID")
    approved_at = Column(DateTime, nullable=True, comment="审批时间")
    
    # Modification Tracking
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    updated_at = Column(DateTime, nullable=True, comment="更新时间")
    original_score = Column(Float, nullable=True, comment="原始分数")
    modification_reason = Column(Text, nullable=True, comment="修改原因")
    
    # Additional Information
    comments = Column(Text, nullable=True, comment="评语")
    feedback = Column(Text, nullable=True, comment="反馈")
    submission_date = Column(DateTime, nullable=True, comment="提交日期")
    grading_date = Column(DateTime, nullable=True, comment="评分日期")

    # Relationships
    student = relationship("User", foreign_keys=[student_id], back_populates="grades")
    course = relationship("Course", back_populates="grades")
    submitter = relationship("User", foreign_keys=[submitted_by])
    approver = relationship("User", foreign_keys=[approved_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('score >= 0 AND score <= max_score', name='check_score_range'),
        CheckConstraint('max_score > 0', name='check_max_score_positive'),
        CheckConstraint('percentage >= 0 AND percentage <= 100', name='check_percentage_range'),
        CheckConstraint('gpa_points >= 0 AND gpa_points <= 4.0', name='check_gpa_points_range'),
        CheckConstraint('grade_points >= 0 AND grade_points <= 4.0', name='check_grade_points_range'),
        CheckConstraint('weight >= 0 AND weight <= 1', name='check_weight_range'),
        Index('idx_grade_student_course', 'student_id', 'course_id'),
        Index('idx_grade_student_semester', 'student_id', 'semester', 'academic_year'),
        Index('idx_grade_course_type', 'course_id', 'grade_type'),
        Index('idx_grade_status', 'status', 'is_published'),
        Index('idx_grade_submitted', 'submitted_by', 'submitted_at'),
        Index('idx_grade_academic', 'academic_year', 'semester'),
    )

    def calculate_gpa_points(self):
        """Calculate GPA points based on Chinese 4.0 scale"""
        if self.score is None:
            return None
        
        percentage = (self.score / self.max_score) * 100
        
        if percentage >= 90:
            return 4.0
        elif percentage >= 85:
            return 3.7
        elif percentage >= 82:
            return 3.3
        elif percentage >= 78:
            return 3.0
        elif percentage >= 75:
            return 2.7
        elif percentage >= 72:
            return 2.3
        elif percentage >= 68:
            return 2.0
        elif percentage >= 64:
            return 1.5
        elif percentage >= 60:
            return 1.0
        else:
            return 0.0

    def calculate_letter_grade(self):
        """Calculate letter grade based on score percentage"""
        if self.score is None:
            return None
        
        percentage = (self.score / self.max_score) * 100
        
        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"

    def calculate_grade_points(self):
        """Calculate grade points for Chinese university system"""
        if self.score is None:
            return None
        
        percentage = (self.score / self.max_score) * 100
        
        if percentage >= 95:
            return 4.0
        elif percentage >= 90:
            return 3.8
        elif percentage >= 85:
            return 3.6
        elif percentage >= 80:
            return 3.2
        elif percentage >= 75:
            return 2.8
        elif percentage >= 70:
            return 2.4
        elif percentage >= 65:
            return 2.0
        elif percentage >= 60:
            return 1.6
        else:
            return 0.0

    def __repr__(self):
        return f"<Grade(id={self.id}, student_id={self.student_id}, course_id={self.course_id}, score={self.score})>"
