from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class StudentScheduleResponse(BaseModel):
    """学生课程表响应模型"""
    student_id: int
    academic_year: str
    semester: str
    schedule: List[Dict[str, Any]]  # 包含课程时间、地点、教师等信息
    total_credits: int
    weekly_hours: int

    class Config:
        from_attributes = True


class AcademicSummaryResponse(BaseModel):
    """学业汇总响应模型"""
    student_id: int
    academic_year: str
    semester: str
    total_credits: int
    earned_credits: int
    gpa: float
    courses_count: int
    passed_courses: int
    failed_courses: int
    average_score: float
    class_ranking: Optional[int] = None
    class_size: Optional[int] = None

    class Config:
        from_attributes = True


class CreditsResponse(BaseModel):
    """学分统计响应模型"""
    student_id: int
    total_credits: int
    earned_credits: int
    in_progress_credits: int
    required_credits: int
    elective_credits: int
    general_credits: int
    professional_credits: int
    credits_by_department: Dict[str, int]
    credits_by_type: Dict[str, int]
    graduation_progress: float

    class Config:
        from_attributes = True


class ClassRankingsResponse(BaseModel):
    """班级排名响应模型"""
    student_id: int
    class_name: str
    current_gpa_rank: int
    current_score_rank: int
    total_students: int
    gpa_percentile: float
    score_percentile: float
    last_semester_gpa_rank: Optional[int] = None
    last_semester_score_rank: Optional[int] = None
    rank_change_gpa: Optional[int] = None
    rank_change_score: Optional[int] = None

    class Config:
        from_attributes = True


class GraduationRequirementsResponse(BaseModel):
    """毕业要求进度响应模型"""
    student_id: int
    total_required_credits: int
    current_credits: int
    remaining_credits: int
    completion_percentage: float
    requirements: List[Dict[str, Any]]
    missing_requirements: List[Dict[str, Any]]
    estimated_graduation_date: Optional[datetime] = None
    on_track: bool
    warnings: List[str]

    class Config:
        from_attributes = True


class TranscriptDataResponse(BaseModel):
    """成绩单数据响应模型"""
    student_info: Dict[str, Any]
    academic_records: List[Dict[str, Any]]
    gpa_summary: Dict[str, Any]
    credits_summary: Dict[str, Any]
    rankings: Optional[List[Dict[str, Any]]] = None
    honors: Optional[List[str]] = None
    graduation_status: Optional[Dict[str, Any]] = None
    generated_at: datetime

    class Config:
        from_attributes = True


class LearningProgressResponse(BaseModel):
    """学习进度响应模型"""
    student_id: int
    course_id: int
    course_name: str
    overall_progress: float
    attendance_rate: Optional[float] = None
    assignment_completion_rate: float
    quiz_performance: float
    current_grade: Optional[float] = None
    predicted_grade: Optional[float] = None
    areas_of_improvement: List[str]
    strengths: List[str]
    last_updated: datetime

    class Config:
        from_attributes = True


class StudyRecommendationResponse(BaseModel):
    """学习建议响应模型"""
    student_id: int
    academic_year: str
    semester: str
    overall_performance: str
    strengths: List[str]
    improvement_areas: List[str]
    study_strategies: List[str]
    recommended_courses: List[Dict[str, Any]]
    time_management_tips: List[str]
    resource_recommendations: List[Dict[str, Any]]
    generated_at: datetime

    class Config:
        from_attributes = True


class AcademicCalendarResponse(BaseModel):
    """学术日历响应模型"""
    student_id: int
    academic_year: str
    important_dates: List[Dict[str, Any]]
    current_semester: Dict[str, Any]
    upcoming_events: List[Dict[str, Any]]
    deadlines: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class AttendanceSummaryResponse(BaseModel):
    """出勤汇总响应模型"""
    student_id: int
    academic_year: str
    semester: str
    total_classes: int
    attended_classes: int
    absent_classes: int
    attendance_rate: float
    course_attendance: List[Dict[str, Any]]
    attendance_trend: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class PerformanceTrendResponse(BaseModel):
    """表现趋势响应模型"""
    student_id: int
    time_period: str
    metrics: Dict[str, List[float]]
    trends: Dict[str, str]  # "improving", "stable", "declining"
    insights: List[str]
    recommendations: List[str]

    class Config:
        from_attributes = True


class CourseLoadAnalysisResponse(BaseModel):
    """课程负担分析响应模型"""
    student_id: int
    current_semester: Dict[str, Any]
    difficulty_distribution: Dict[str, int]
    weekly_study_hours: int
    workload_balance_score: float
    recommendations: List[str]
    potential_overload_courses: List[str]
    underutilized_capacity: List[str]

    class Config:
        from_attributes = True