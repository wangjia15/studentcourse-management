import enum

from sqlalchemy import Column, ForeignKey, Integer, String, Text
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


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)  # user, course, grade
    resource_id = Column(Integer, nullable=True)
    old_values = Column(Text, nullable=True)  # JSON string
    new_values = Column(Text, nullable=True)  # JSON string
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
