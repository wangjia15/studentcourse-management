from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ReportType(str, Enum):
    TRANSCRIPT = "transcript"
    CLASS_SUMMARY = "class_summary"
    GRADE_ANALYSIS = "grade_analysis"
    GPA_REPORT = "gpa_report"
    ATTENDANCE_REPORT = "attendance_report"


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"
    CSV = "csv"


class ReportRequest(BaseModel):
    """报告请求基类"""
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    include_details: bool = False
    custom_parameters: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TranscriptRequest(ReportRequest):
    """成绩单请求模型"""
    student_id: int
    include_all_semesters: bool = True
    include_gpa_details: bool = True
    include_rankings: bool = False
    language: str = Field("zh", description="语言: zh, en")
    template_type: str = Field("standard", description="模板类型: standard, detailed, simple")

    class Config:
        from_attributes = True


class ClassSummaryRequest(ReportRequest):
    """班级汇总请求模型"""
    class_id: str
    include_individual_grades: bool = False
    include_statistics: bool = True
    include_rankings: bool = True
    group_by_subject: bool = False
    include_attendance: bool = False

    class Config:
        from_attributes = True


class GradeAnalysisRequest(ReportRequest):
    """成绩分析请求模型"""
    analysis_scope: str = Field(..., description="分析范围: course, class, department, grade")
    scope_id: Optional[str] = None  # 根据analysis_scope确定具体ID
    course_id: Optional[int] = None
    include_trends: bool = True
    include_distributions: bool = True
    include_comparisons: bool = True
    comparison_period: Optional[str] = None  # 对比时期

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    """报告响应模型"""
    id: int
    report_type: ReportType
    status: ReportStatus
    format: ReportFormat
    requested_by: int
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    progress: int = Field(0, ge=0, le=100)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    download_count: int = 0
    max_downloads: int = 5

    class Config:
        from_attributes = True


class ReportStatusResponse(BaseModel):
    """报告状态响应模型"""
    report_id: int
    status: ReportStatus
    progress: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    estimated_completion: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportDownloadResponse(BaseModel):
    """报告下载响应模型"""
    report_id: int
    download_url: str
    file_name: str
    file_size: int
    file_type: str
    expires_at: datetime
    remaining_downloads: int

    class Config:
        from_attributes = True


class ReportTemplateResponse(BaseModel):
    """报告模板响应模型"""
    id: int
    name: str
    description: str
    report_type: ReportType
    template_path: str
    is_default: bool
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportConfigResponse(BaseModel):
    """报告配置响应模型"""
    max_file_size: int
    allowed_formats: List[ReportFormat]
    default_retention_days: int
    max_concurrent_reports: int
    cleanup_interval_hours: int

    class Config:
        from_attributes = True


class ReportStatisticsResponse(BaseModel):
    """报告统计响应模型"""
    total_reports: int
    reports_by_type: Dict[str, int]
    reports_by_status: Dict[str, int]
    reports_by_format: Dict[str, int]
    average_processing_time: float
    success_rate: float
    most_requested_type: str
    generation_trend: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class ScheduleReportRequest(BaseModel):
    """定时报告请求模型"""
    name: str
    report_type: ReportType
    schedule_expression: str  # Cron表达式
    report_parameters: Dict[str, Any]
    recipients: List[str]
    is_active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleReportResponse(BaseModel):
    """定时报告响应模型"""
    id: int
    name: str
    report_type: ReportType
    schedule_expression: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportAuditLogResponse(BaseModel):
    """报告审计日志响应模型"""
    id: int
    report_id: Optional[int] = None
    action: str
    user_id: int
    user_name: str
    ip_address: str
    user_agent: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BulkReportRequest(BaseModel):
    """批量报告请求模型"""
    report_type: ReportType
    student_ids: Optional[List[int]] = None
    class_ids: Optional[List[str]] = None
    course_ids: Optional[List[int]] = None
    common_parameters: Dict[str, Any]
    format: ReportFormat = ReportFormat.PDF
    send_email: bool = False
    email_subject: Optional[str] = None
    email_body: Optional[str] = None

    class Config:
        from_attributes = True


class BulkReportResponse(BaseModel):
    """批量报告响应模型"""
    batch_id: str
    total_requests: int
    completed_requests: int
    failed_requests: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None

    class Config:
        from_attributes = True