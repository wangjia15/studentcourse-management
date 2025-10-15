from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class GPACalculationResponse(BaseModel):
    """GPA计算响应模型"""
    student_id: int
    student_name: str
    total_gpa: float
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    total_credits: int
    total_courses: int
    grade_breakdown: Dict[str, int]  # 成绩等级分布
    calculation_date: datetime

    class Config:
        from_attributes = True


class GradeDistributionResponse(BaseModel):
    """成绩分布响应模型"""
    course_id: int
    course_name: str
    total_students: int
    grade_distribution: Dict[str, int]  # A, B, C, D, F 分布
    score_distribution: Dict[str, int]  # 分数段分布 (90-100, 80-89, etc.)
    average_score: float
    median_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float  # 及格率
    excellent_rate: float  # 优秀率 (85分以上)

    class Config:
        from_attributes = True


class StudentTrendResponse(BaseModel):
    """学生成绩趋势响应模型"""
    student_id: int
    student_name: str
    trends: List[Dict[str, Any]]  # 每个学期的成绩趋势
    overall_trend: str  # "improving", "stable", "declining"
    average_gpa_trend: List[float]  # GPA趋势
    credit_earning_trend: List[int]  # 获得学分趋势

    class Config:
        from_attributes = True


class SemesterComparisonResponse(BaseModel):
    """学期对比响应模型"""
    comparison_type: str  # "individual", "class", "department"
    semester1_data: Dict[str, Any]
    semester2_data: Dict[str, Any]
    improvements: List[str]
    declines: List[str]
    analysis_summary: str
    statistical_significance: Optional[float] = None

    class Config:
        from_attributes = True


class ClassRankingResponse(BaseModel):
    """班级排名响应模型"""
    student_id: int
    student_name: str
    class_name: str
    gpa_rank: int
    total_students: int
    gpa_percentile: float
    current_gpa: float
    class_average_gpa: float
    rank_change: Optional[int] = None  # 相比上次排名变化

    class Config:
        from_attributes = True


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
    grade_distribution: Dict[str, int]
    score_ranges: Dict[str, int]

    class Config:
        from_attributes = True


class PerformanceMetricsResponse(BaseModel):
    """学习表现指标响应模型"""
    student_id: int
    academic_year: str
    semester: str
    attendance_rate: Optional[float] = None
    assignment_completion_rate: Optional[float] = None
    participation_score: Optional[float] = None
    improvement_score: Optional[float] = None
    consistency_score: Optional[float] = None
    overall_performance_score: float

    class Config:
        from_attributes = True


class CourseAnalyticsRequest(BaseModel):
    """课程分析请求模型"""
    course_id: int
    analysis_type: str = Field(..., description="分析类型: distribution, trends, comparison")
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    include_details: bool = False

    class Config:
        from_attributes = True


class LearningAnalyticsResponse(BaseModel):
    """学习分析响应模型"""
    student_id: int
    learning_style: Optional[str] = None
    strength_areas: List[str]
    improvement_areas: List[str]
    study_recommendations: List[str]
    predicted_performance: Optional[float] = None
    risk_factors: List[str]

    class Config:
        from_attributes = True


class BatchAnalyticsRequest(BaseModel):
    """批量分析请求模型"""
    student_ids: List[int]
    analysis_types: List[str]
    academic_year: Optional[str] = None
    semester: Optional[str] = None

    class Config:
        from_attributes = True


class BatchAnalyticsResponse(BaseModel):
    """批量分析响应模型"""
    total_students: int
    processed_students: int
    results: List[Dict[str, Any]]
    summary_statistics: Dict[str, Any]
    processing_time: float

    class Config:
        from_attributes = True