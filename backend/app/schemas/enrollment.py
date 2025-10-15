from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class EnrollmentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    COMPLETED = "completed"


class EnrollmentRequest(BaseModel):
    """选课请求模型"""
    course_id: int
    student_id: Optional[int] = None  # 如果不提供则使用当前用户
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    reason: Optional[str] = None
    is_priority: bool = False

    class Config:
        from_attributes = True


class EnrollmentResponse(BaseModel):
    """选课响应模型"""
    id: int
    course_id: int
    student_id: int
    academic_year: str
    semester: str
    status: EnrollmentStatus
    enrolled_at: datetime
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    withdrawal_date: Optional[datetime] = None
    withdrawal_reason: Optional[str] = None
    final_grade: Optional[float] = None
    credits_earned: Optional[int] = None
    attendance_rate: Optional[float] = None

    class Config:
        from_attributes = True


class StudentListResponse(BaseModel):
    """学生列表响应模型"""
    students: List[dict]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True


class StudentImportResponse(BaseModel):
    """学生导入响应模型"""
    total_records: int
    successful_imports: int
    failed_imports: int
    errors: List[str]
    imported_students: List[dict]

    class Config:
        from_attributes = True


class EnrollmentHistoryResponse(BaseModel):
    """选课历史响应模型"""
    id: int
    course_id: int
    course_code: str
    course_name: str
    credits: int
    academic_year: str
    semester: str
    status: EnrollmentStatus
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    final_grade: Optional[float] = None
    letter_grade: Optional[str] = None
    gpa_points: Optional[float] = None

    class Config:
        from_attributes = True


class CourseEnrollmentStatsResponse(BaseModel):
    """课程选课统计响应模型"""
    course_id: int
    course_name: str
    max_students: int
    current_enrolled: int
    available_spots: int
    enrollment_rate: float
    waitlist_count: int
    academic_year: str
    semester: str

    class Config:
        from_attributes = True


class BatchEnrollmentRequest(BaseModel):
    """批量选课请求模型"""
    course_ids: List[int]
    student_ids: Optional[List[int]] = None  # 如果不提供则使用当前用户
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    override_conflicts: bool = False
    override_prerequisites: bool = False

    class Config:
        from_attributes = True


class BatchEnrollmentResponse(BaseModel):
    """批量选课响应模型"""
    successful_enrollments: List[EnrollmentResponse]
    failed_enrollments: List[dict]
    conflicts: List[dict]
    total_processed: int
    success_count: int
    failure_count: int

    class Config:
        from_attributes = True


class EnrollmentConflictResponse(BaseModel):
    """选课冲突响应模型"""
    conflict_type: str  # "schedule", "prerequisite", "capacity", "duplicate"
    course_id: int
    conflicting_course_id: Optional[int] = None
    message: str
    resolution_options: List[str]

    class Config:
        from_attributes = True


class WaitlistRequest(BaseModel):
    """候补请求模型"""
    course_id: int
    priority_reason: Optional[str] = None
    contact_method: str = Field("email", description="联系方式: email, phone, both")

    class Config:
        from_attributes = True


class WaitlistResponse(BaseModel):
    """候补响应模型"""
    id: int
    course_id: int
    student_id: int
    position: int
    status: str  # "active", "offered", "accepted", "declined", "expired"
    created_at: datetime
    offered_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EnrollmentApprovalRequest(BaseModel):
    """选课审批请求模型"""
    enrollment_ids: List[int]
    action: str = Field(..., description="操作: approve, reject")
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class EnrollmentApprovalResponse(BaseModel):
    """选课审批响应模型"""
    processed_enrollments: List[EnrollmentResponse]
    successful_approvals: int
    successful_rejections: int
    errors: List[str]

    class Config:
        from_attributes = True


class EnrollmentPrerequisiteCheckResponse(BaseModel):
    """选课先修条件检查响应模型"""
    course_id: int
    meets_prerequisites: bool
    missing_prerequisites: List[dict]
    waiver_available: bool
    waiver_reason: Optional[str] = None

    class Config:
        from_attributes = True


class EnrollmentScheduleConflictResponse(BaseModel):
    """选课时间冲突检查响应模型"""
    has_conflicts: bool
    conflicts: List[dict]
    alternative_sections: List[dict]

    class Config:
        from_attributes = True