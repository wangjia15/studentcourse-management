from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class CourseType(str, Enum):
    REQUIRED = "required"
    ELECTIVE = "elective"
    PROFESSIONAL = "professional"
    GENERAL = "general"


class CourseStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CourseBase(BaseModel):
    """课程基础模型"""
    course_code: str = Field(..., description="课程代码")
    course_name: str = Field(..., description="课程名称")
    course_name_en: Optional[str] = Field(None, description="英文名称")
    description: Optional[str] = Field(None, description="课程描述")
    course_type: CourseType = Field(CourseType.REQUIRED, description="课程类型")
    credits: int = Field(3, ge=1, le=10, description="学分")
    hours: int = Field(48, ge=1, le=200, description="学时")
    academic_year: str = Field(..., description="学年")
    semester: str = Field(..., description="学期")
    max_students: int = Field(50, ge=1, le=500, description="最大学生数")
    department: str = Field(..., description="开课院系")
    classroom: Optional[str] = Field(None, description="教室")
    schedule_info: Optional[str] = Field(None, description="上课时间地点信息")
    exam_time: Optional[str] = Field(None, description="考试时间")
    exam_location: Optional[str] = Field(None, description="考试地点")
    grading_method: Optional[str] = Field(None, description="评分方式")
    passing_score: int = Field(60, ge=0, le=100, description="及格分数")

    class Config:
        from_attributes = True


class CourseCreate(CourseBase):
    """创建课程请求模型"""
    teacher_id: Optional[int] = Field(None, description="授课教师ID")
    teaching_assistant_id: Optional[int] = Field(None, description="助教ID")


class CourseUpdate(BaseModel):
    """更新课程请求模型"""
    course_name: Optional[str] = Field(None, description="课程名称")
    course_name_en: Optional[str] = Field(None, description="英文名称")
    description: Optional[str] = Field(None, description="课程描述")
    credits: Optional[int] = Field(None, ge=1, le=10, description="学分")
    hours: Optional[int] = Field(None, ge=1, le=200, description="学时")
    max_students: Optional[int] = Field(None, ge=1, le=500, description="最大学生数")
    classroom: Optional[str] = Field(None, description="教室")
    schedule_info: Optional[str] = Field(None, description="上课时间地点信息")
    exam_time: Optional[str] = Field(None, description="考试时间")
    exam_location: Optional[str] = Field(None, description="考试地点")
    grading_method: Optional[str] = Field(None, description="评分方式")
    passing_score: Optional[int] = Field(None, ge=0, le=100, description="及格分数")
    status: Optional[CourseStatus] = Field(None, description="课程状态")
    is_active: Optional[bool] = Field(None, description="是否激活")

    class Config:
        from_attributes = True


class CourseResponse(CourseBase):
    """课程响应模型"""
    id: int
    teacher_id: int
    teaching_assistant_id: Optional[int] = None
    current_enrolled: int
    min_students: int
    status: CourseStatus
    is_active: bool
    faculty_responsible: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 向后兼容
Course = CourseResponse
