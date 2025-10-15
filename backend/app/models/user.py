import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text, Index
from sqlalchemy.orm import relationship

from .base import BaseModel


class UserRole(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher" 
    STUDENT = "student"


class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"


class User(BaseModel):
    __tablename__ = "users"

    # Basic Information
    email = Column(String(255), unique=True, index=True, nullable=False, comment="用户邮箱")
    username = Column(String(100), unique=True, index=True, nullable=False, comment="用户名")
    full_name = Column(String(100), nullable=False, comment="中文姓名")
    
    # University Specific Fields
    student_id = Column(String(20), unique=True, index=True, nullable=True, comment="学号")
    faculty_id = Column(String(20), unique=True, index=True, nullable=True, comment="教师工号")
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT, comment="用户角色")
    department = Column(String(100), nullable=False, comment="院系")
    major = Column(String(100), nullable=True, comment="专业")
    class_name = Column(String(50), nullable=True, comment="班级")
    
    # Academic Information
    enrollment_year = Column(String(4), nullable=True, comment="入学年份")
    graduation_year = Column(String(4), nullable=True, comment="毕业年份")
    academic_year = Column(String(9), nullable=True, comment="学年 (e.g., 2024-2025)")
    semester = Column(String(20), nullable=True, comment="学期 (e.g., Fall, Spring)")
    
    # Authentication Fields
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False, comment="用户状态")
    
    # Contact Information
    phone = Column(String(20), nullable=True, comment="电话号码")
    address = Column(Text, nullable=True, comment="地址")
    
    # System Fields
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    failed_login_attempts = Column(String(3), default=0, nullable=False, comment="失败登录次数")
    locked_until = Column(DateTime, nullable=True, comment="锁定到期时间")

    # Relationships
    taught_courses = relationship("Course", back_populates="teacher")
    grades = relationship("Grade", back_populates="student")
    enrollments = relationship("Enrollment", back_populates="student")
    audit_logs = relationship("AuditLog", back_populates="user")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_student_id', 'student_id'),
        Index('idx_user_faculty_id', 'faculty_id'),
        Index('idx_user_role_department', 'role', 'department'),
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_name_department', 'full_name', 'department'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"
