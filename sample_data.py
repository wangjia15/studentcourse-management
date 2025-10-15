#!/usr/bin/env python3
"""
Sample data creation script for Chinese University Grade Management System
"""

import sys
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import User, Course, Enrollment, Grade, AuditLog
from app.db.database import SessionLocal, engine
from app.models.base import Base

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_sample_data():
    """Create sample data for testing"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Creating sample data...")
        
        # Create admin user
        admin = User(
            email="admin@university.edu.cn",
            username="admin",
            full_name="系统管理员",
            role="admin",
            department="信息中心",
            password_hash=pwd_context.hash("admin123"),
            is_active=True,
            status="active"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        # Create teacher
        teacher = User(
            email="zhang.wei@university.edu.cn",
            username="zhangwei",
            full_name="张伟",
            faculty_id="T001",
            role="teacher",
            department="计算机科学与技术学院",
            password_hash=pwd_context.hash("teacher123"),
            is_active=True,
            status="active"
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        
        # Create student
        student = User(
            email="chen.jie@university.edu.cn",
            username="chenjie",
            full_name="陈杰",
            student_id="2024001",
            role="student",
            department="计算机科学与技术学院",
            password_hash=pwd_context.hash("student123"),
            is_active=True,
            status="active"
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        
        # Create course
        course = Course(
            course_code="CS301",
            course_name="数据结构与算法",
            description="本课程介绍基本的数据结构和算法",
            credits=4,
            hours=64,
            academic_year="2024-2025",
            semester="Fall",
            max_students=50,
            teacher_id=teacher.id,
            department="计算机科学与技术学院"
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        
        # Create enrollment
        enrollment = Enrollment(
            student_id=student.id,
            course_id=course.id,
            status="enrolled",
            is_active=True,
            enrolled_at=datetime.now(),
            academic_year="2024-2025",
            semester="Fall"
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        
        # Create grade
        grade = Grade(
            student_id=student.id,
            course_id=course.id,
            score=85.0,
            max_score=100.0,
            grade_type="midterm",
            weight=0.3,
            academic_year="2024-2025",
            semester="Fall",
            status="approved",
            submitted_by=teacher.id,
            submitted_at=datetime.now()
        )
        db.add(grade)
        db.commit()
        
        # Create audit log
        audit_log = AuditLog(
            action="create",
            table_name="users",
            record_id=admin.id,
            user_id=admin.id,
            description="创建管理员用户",
            timestamp=datetime.now()
        )
        db.add(audit_log)
        db.commit()
        
        print("✅ Sample data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
