import enum
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import relationship

from .base import BaseModel


class AuditAction(enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    GRADE_IMPORT = "grade_import"
    GRADE_EXPORT = "grade_export"
    ENROLL = "enroll"
    DROP = "drop"
    APPROVE = "approve"
    REJECT = "reject"


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    # Action Information
    action = Column(String(50), nullable=False, comment="操作类型")
    table_name = Column(String(50), nullable=False, comment="表名")
    record_id = Column(Integer, nullable=True, comment="记录ID")
    
    # User Information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    user_role = Column(String(20), nullable=True, comment="用户角色")
    
    # Request Information
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    
    # Change Tracking
    old_values = Column(Text, nullable=True, comment="旧值")
    new_values = Column(Text, nullable=True, comment="新值")
    changed_fields = Column(Text, nullable=True, comment="变更字段")
    
    # Status and Result
    status = Column(String(20), default="success", nullable=False, comment="操作状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # Additional Information
    description = Column(Text, nullable=True, comment="描述")
    module = Column(String(50), nullable=True, comment="模块")
    
    # Timing Information
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment="时间戳")
    duration_ms = Column(Integer, nullable=True, comment="执行时长(毫秒)")

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_table_record', 'table_name', 'record_id'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_status', 'status'),
        Index('idx_audit_module', 'module'),
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_table_action', 'table_name', 'action'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', table='{self.table_name}', user_id={self.user_id})>"
