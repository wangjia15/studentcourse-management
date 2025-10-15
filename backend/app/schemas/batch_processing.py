from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from .batch_processing import ValidationLevel, ProcessingStatus


class FileUploadRequest(BaseModel):
    """文件上传请求模型"""
    file_type: Optional[str] = Field(None, description="文件类型 (excel/csv)")
    sheet_name: Optional[str] = Field(None, description="Excel工作表名称")
    skip_duplicates: bool = Field(True, description="是否跳过重复记录")
    validate_only: bool = Field(False, description="仅验证数据，不实际导入")
    auto_detect_format: bool = Field(True, description="自动检测文件格式")


class ValidationErrorResponse(BaseModel):
    """验证错误响应模型"""
    row_number: int = Field(..., description="行号")
    field: str = Field(..., description="字段名")
    message: str = Field(..., description="错误信息")
    level: ValidationLevel = Field(..., description="错误级别")
    current_value: Any = Field(None, description="当前值")
    suggested_value: Any = Field(None, description="建议值")


class BatchProcessingResponse(BaseModel):
    """批量处理响应模型"""
    task_id: Optional[str] = Field(None, description="任务ID")
    status: ProcessingStatus = Field(..., description="处理状态")
    total_records: int = Field(..., description="总记录数")
    processed_records: int = Field(..., description="已处理记录数")
    successful_records: int = Field(..., description="成功记录数")
    failed_records: int = Field(..., description="失败记录数")
    duplicate_records: int = Field(..., description="重复记录数")
    warnings: List[ValidationErrorResponse] = Field(default_factory=list, description="警告信息")
    errors: List[ValidationErrorResponse] = Field(default_factory=list, description="错误信息")
    processing_time: float = Field(..., description="处理时间(秒)")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    file_path: Optional[str] = Field(None, description="原文件路径")
    export_file_path: Optional[str] = Field(None, description="导出文件路径")


class TemplateRequest(BaseModel):
    """模板请求模型"""
    template_type: str = Field("basic", description="模板类型")
    format: str = Field("excel", description="导出格式")


class ExportRequest(BaseModel):
    """导出请求模型"""
    course_id: Optional[int] = Field(None, description="课程ID")
    academic_year: Optional[str] = Field(None, description="学年")
    semester: Optional[str] = Field(None, description="学期")
    grade_type: Optional[str] = Field(None, description="成绩类型")
    format: str = Field("excel", description="导出格式")
    include_details: bool = Field(True, description="包含详细信息")
    filter_conditions: Optional[Dict[str, Any]] = Field(None, description="筛选条件")


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: ProcessingStatus = Field(..., description="处理状态")
    progress: float = Field(..., description="进度百分比")
    current_stage: str = Field(..., description="当前阶段")
    estimated_remaining_time: Optional[int] = Field(None, description="预计剩余时间(秒)")
    error_message: Optional[str] = Field(None, description="错误信息")
    result: Optional[BatchProcessingResponse] = Field(None, description="处理结果")


class BatchStatisticsResponse(BaseModel):
    """批量统计响应模型"""
    total_files_processed: int = Field(..., description="总处理文件数")
    total_records_processed: int = Field(..., description="总处理记录数")
    success_rate: float = Field(..., description="成功率")
    average_processing_time: float = Field(..., description="平均处理时间")
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list, description="最近活动")
    error_distribution: Dict[str, int] = Field(default_factory=dict, description="错误分布")


class DataValidationRule(BaseModel):
    """数据验证规则模型"""
    field_name: str = Field(..., description="字段名")
    rule_type: str = Field(..., description="规则类型")
    parameters: Dict[str, Any] = Field(..., description="规则参数")
    error_message: str = Field(..., description="错误信息")
    is_active: bool = Field(True, description="是否激活")


class ImportPreviewResponse(BaseModel):
    """导入预览响应模型"""
    file_info: Dict[str, Any] = Field(..., description="文件信息")
    column_mapping: Dict[str, str] = Field(..., description="列映射")
    sample_data: List[Dict[str, Any]] = Field(..., description="示例数据")
    detected_format: str = Field(..., description="检测到的格式")
    estimated_records: int = Field(..., description="预计记录数")
    potential_issues: List[str] = Field(default_factory=list, description="潜在问题")


class ProcessingOptions(BaseModel):
    """处理选项模型"""
    skip_invalid_records: bool = Field(True, description="跳过无效记录")
    max_errors: int = Field(1000, description="最大错误数")
    chunk_size: int = Field(1000, description="批处理大小")
    enable_parallel_processing: bool = Field(True, description="启用并行处理")
    notification_on_completion: bool = Field(False, description="完成时通知")
    backup_before_import: bool = Field(True, description="导入前备份")


class ScheduleBatchJobRequest(BaseModel):
    """定时批量任务请求模型"""
    job_name: str = Field(..., description="任务名称")
    schedule_type: str = Field(..., description="调度类型")
    schedule_config: Dict[str, Any] = Field(..., description="调度配置")
    source_path: str = Field(..., description="源文件路径")
    processing_options: ProcessingOptions = Field(..., description="处理选项")
    notification_emails: List[str] = Field(default_factory=list, description="通知邮箱")


class BatchJobResponse(BaseModel):
    """批量任务响应模型"""
    job_id: str = Field(..., description="任务ID")
    job_name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务状态")
    schedule_info: Dict[str, Any] = Field(..., description="调度信息")
    last_run: Optional[datetime] = Field(None, description="上次运行时间")
    next_run: Optional[datetime] = Field(None, description="下次运行时间")
    run_count: int = Field(..., description="运行次数")
    success_count: int = Field(..., description="成功次数")
    failure_count: int = Field(..., description="失败次数")


class FileProcessingConfig(BaseModel):
    """文件处理配置模型"""
    supported_formats: List[str] = Field(default_factory=lambda: ["excel", "csv"], description="支持的格式")
    max_file_size: int = Field(100 * 1024 * 1024, description="最大文件大小(字节)")
    chunk_size: int = Field(5000, description="分块大小")
    timeout_seconds: int = Field(600, description="超时时间(秒)")
    retry_attempts: int = Field(3, description="重试次数")
    encoding_detection: bool = Field(True, description="编码检测")
    delimiter_detection: bool = Field(True, description="分隔符检测")