from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SystemStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BackupStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SystemHealthResponse(BaseModel):
    """系统健康状态响应模型"""
    status: SystemStatus
    timestamp: datetime
    services: Dict[str, Dict[str, Any]]
    database_status: Dict[str, Any]
    resource_usage: Dict[str, Any]
    last_restart: Optional[datetime] = None
    uptime_seconds: int
    error_count_24h: int
    warning_count_24h: int

    class Config:
        from_attributes = True


class SystemMetricsResponse(BaseModel):
    """系统性能指标响应模型"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: Dict[str, Any]
    disk_usage: Dict[str, Any]
    network_io: Dict[str, Any]
    database_metrics: Dict[str, Any]
    api_metrics: Dict[str, Any]
    active_sessions: int
    request_count_1h: int
    average_response_time: float
    error_rate_1h: float

    class Config:
        from_attributes = True


class BackupRequest(BaseModel):
    """备份请求模型"""
    backup_type: str = Field(..., description="备份类型: full, incremental, differential")
    description: Optional[str] = None
    include_files: bool = True
    include_database: bool = True
    compression: bool = True
    encryption: bool = False
    retention_days: int = Field(30, description="保留天数")
    destination_path: Optional[str] = None

    class Config:
        from_attributes = True


class BackupResponse(BaseModel):
    """备份响应模型"""
    id: int
    backup_type: str
    status: BackupStatus
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    progress: int = Field(0, ge=0, le=100)
    created_by: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    checksum: Optional[str] = None

    class Config:
        from_attributes = True


class RestoreRequest(BaseModel):
    """恢复请求模型"""
    backup_id: int
    restore_type: str = Field(..., description="恢复类型: full, selective")
    target_data: Optional[List[str]] = None  # 选择性恢复的数据类型
    confirm_restore: bool = Field(False, description="确认恢复操作")
    create_backup_before_restore: bool = True

    class Config:
        from_attributes = True


class RestoreResponse(BaseModel):
    """恢复响应模型"""
    id: int
    backup_id: int
    status: str
    restore_type: str
    progress: int = Field(0, ge=0, le=100)
    created_by: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    restored_items: List[str] = []

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """审计日志响应模型"""
    id: int
    user_id: int
    username: str
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    ip_address: str
    user_agent: str
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    response_status: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SystemConfigResponse(BaseModel):
    """系统配置响应模型"""
    id: int
    config_key: str
    config_value: str
    config_type: str
    description: str
    is_sensitive: bool
    is_public: bool
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SystemConfigUpdate(BaseModel):
    """系统配置更新模型"""
    config_value: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserSessionResponse(BaseModel):
    """用户会话响应模型"""
    id: int
    user_id: int
    username: str
    ip_address: str
    user_agent: str
    login_time: datetime
    last_activity: datetime
    is_active: bool
    session_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SystemLogResponse(BaseModel):
    """系统日志响应模型"""
    id: int
    level: str
    logger_name: str
    message: str
    module: Optional[str] = None
    function_name: Optional[str] = None
    line_number: Optional[int] = None
    timestamp: datetime
    extra_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class MaintenanceModeResponse(BaseModel):
    """维护模式响应模型"""
    is_enabled: bool
    message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    enabled_by: Optional[int] = None
    enabled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CacheInfoResponse(BaseModel):
    """缓存信息响应模型"""
    cache_type: str
    total_keys: int
    memory_usage: int
    hit_rate: float
    miss_rate: float
    eviction_count: int
    last_cleanup: Optional[datetime] = None

    class Config:
        from_attributes = True


class DatabaseStatsResponse(BaseModel):
    """数据库统计响应模型"""
    total_tables: int
    total_records: int
    database_size: int
    index_size: int
    connection_count: int
    active_connections: int
    query_count_1h: int
    slow_queries_1h: int
    average_query_time: float

    class Config:
        from_attributes = True


class SecurityIncidentResponse(BaseModel):
    """安全事件响应模型"""
    id: int
    incident_type: str
    severity: str
    description: str
    user_id: Optional[int] = None
    ip_address: str
    user_agent: str
    is_resolved: bool
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PerformanceAlertResponse(BaseModel):
    """性能告警响应模型"""
    id: int
    alert_type: str
    metric_name: str
    threshold_value: float
    current_value: float
    severity: str
    message: str
    is_active: bool
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SystemInfoResponse(BaseModel):
    """系统信息响应模型"""
    version: str
    build_date: Optional[str] = None
    environment: str
    python_version: str
    database_version: str
    operating_system: str
    architecture: str
    hostname: str
    uptime_seconds: int

    class Config:
        from_attributes = True