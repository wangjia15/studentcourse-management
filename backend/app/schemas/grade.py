from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class GradeType(str, Enum):
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    MIDTERM = "midterm"
    FINAL = "final"
    PROJECT = "project"
    PARTICIPATION = "participation"
    LAB = "lab"
    OTHER = "other"


class GradeStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class GradeBase(BaseModel):
    """成绩基础模型"""
    score: float = Field(..., ge=0, description="得分")
    max_score: float = Field(default=100.0, gt=0, description="满分")
    grade_type: GradeType = Field(..., description="成绩类型")
    weight: float = Field(default=1.0, gt=0, le=1, description="权重")
    academic_year: str = Field(..., description="学年")
    semester: str = Field(..., description="学期")
    comments: Optional[str] = Field(None, description="评语")
    feedback: Optional[str] = Field(None, description="反馈")

    class Config:
        from_attributes = True


class GradeCreate(GradeBase):
    """创建成绩请求模型"""
    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="课程ID")


class GradeUpdate(BaseModel):
    """更新成绩请求模型"""
    score: Optional[float] = Field(None, ge=0, description="得分")
    max_score: Optional[float] = Field(None, gt=0, description="满分")
    grade_type: Optional[GradeType] = Field(None, description="成绩类型")
    weight: Optional[float] = Field(None, gt=0, le=1, description="权重")
    comments: Optional[str] = Field(None, description="评语")
    feedback: Optional[str] = Field(None, description="反馈")
    modification_reason: Optional[str] = Field(None, description="修改原因")


class GradeBatchCreate(BaseModel):
    """批量创建成绩请求模型"""
    grades: List[GradeCreate]


class GradeResponse(GradeBase):
    """成绩响应模型"""
    id: int
    student_id: int
    course_id: int
    course_name: Optional[str] = None
    course_code: Optional[str] = None
    percentage: Optional[float] = None
    letter_grade: Optional[str] = None
    gpa_points: Optional[float] = None
    grade_points: Optional[float] = None
    status: GradeStatus
    is_final: bool
    is_published: bool
    submitted_by: int
    submitted_at: datetime
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    original_score: Optional[float] = None
    modification_reason: Optional[str] = None
    submission_date: Optional[datetime] = None
    grading_date: Optional[datetime] = None

    class Config:
        from_attributes = True


# 向后兼容
Grade = GradeResponse


class GradeStatisticsResponse(BaseModel):
    """成绩统计响应模型"""
    total_students: int
    submitted_grades: int
    average_score: float
    median_score: float
    standard_deviation: float
    min_score: float
    max_score: float
    pass_rate: float
    grade_distribution: dict
    score_ranges: dict

    class Config:
        from_attributes = True


class GradeHistoryResponse(BaseModel):
    """成绩历史响应模型"""
    id: int
    grade_id: int
    action: str
    old_score: Optional[float] = None
    new_score: Optional[float] = None
    reason: Optional[str] = None
    changed_by: int
    changed_by_name: str
    changed_at: datetime

    class Config:
        from_attributes = True


class GradeAnalysisResponse(BaseModel):
    """成绩分析响应模型"""
    course_id: int
    course_name: str
    total_students: int
    grade_statistics: GradeStatisticsResponse
    performance_levels: dict  # 优秀、良好、中等、及格、不及格分布
    improvement_suggestions: List[str]
    grade_trends: List[dict]

    class Config:
        from_attributes = True


class ClassGradeResponse(BaseModel):
    """班级成绩响应模型"""
    class_id: str
    class_name: str
    total_students: int
    courses: List[dict]
    average_gpa: float
    pass_rate: float
    excellence_rate: float

    class Config:
        from_attributes = True


class StudentGradeSummaryResponse(BaseModel):
    """学生成绩汇总响应模型"""
    student_id: int
    student_name: str
    academic_year: str
    semester: str
    total_courses: int
    total_credits: int
    gpa: float
    average_score: float
    passed_courses: int
    failed_courses: int
    course_grades: List[GradeResponse]

    class Config:
        from_attributes = True


class GradeDistributionRequest(BaseModel):
    """成绩分布请求模型"""
    course_id: int
    grade_type: Optional[GradeType] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    include_unpublished: bool = False

    class Config:
        from_attributes = True


class GradePublishRequest(BaseModel):
    """成绩发布请求模型"""
    grade_ids: List[int]
    publish_all: bool = False
    course_id: Optional[int] = None
    grade_type: Optional[GradeType] = None
    notification_message: Optional[str] = None

    class Config:
        from_attributes = True
