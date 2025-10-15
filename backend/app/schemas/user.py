from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.core.security import (
    validate_chinese_email,
    validate_chinese_name,
    validate_student_id,
    validate_teacher_id,
)
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    role: UserRole = UserRole.STUDENT
    is_active: bool = True
    is_verified: bool = False
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_chinese_university_email(cls, v: str) -> str:
        if not validate_chinese_email(v):
            raise ValueError("Must be a valid Chinese university email address")
        return v.lower()

    @field_validator("full_name")
    @classmethod
    def validate_chinese_name_format(cls, v: str) -> str:
        if not validate_chinese_name(v):
            raise ValueError("Full name must contain Chinese characters")
        return v.strip()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v.lower()

    @field_validator("student_id")
    @classmethod
    def validate_student_id_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_student_id(v):
            raise ValueError("Invalid student ID format")
        return v

    @field_validator("teacher_id")
    @classmethod
    def validate_teacher_id_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_teacher_id(v):
            raise ValueError("Invalid teacher ID format")
        return v

    @field_validator("username")
    @classmethod
    def check_required_ids(cls, v: str, info) -> str:
        if hasattr(info, "data"):
            data = info.data
            role = data.get("role", UserRole.STUDENT)

            if role == UserRole.STUDENT and not data.get("student_id"):
                raise ValueError("Student ID is required for student role")

            if role == UserRole.TEACHER and not data.get("teacher_id"):
                raise ValueError("Teacher ID is required for teacher role")

        return v


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        from app.core.security import validate_password_strength

        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError("; ".join(errors))
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None
    password: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_chinese_university_email(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_chinese_email(v):
            raise ValueError("Must be a valid Chinese university email address")
        return v.lower() if v else v

    @field_validator("full_name")
    @classmethod
    def validate_chinese_name_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_chinese_name(v):
            raise ValueError("Full name must contain Chinese characters")
        return v.strip() if v else v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v:
            if len(v) < 3 or len(v) > 50:
                raise ValueError("Username must be between 3 and 50 characters")
            if not v.replace("_", "").replace("-", "").isalnum():
                raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
            return v.lower()
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v:
            from app.core.security import validate_password_strength

            is_valid, errors = validate_password_strength(v)
            if not is_valid:
                raise ValueError("; ".join(errors))
        return v

    @field_validator("student_id")
    @classmethod
    def validate_student_id_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_student_id(v):
            raise ValueError("Invalid student ID format")
        return v

    @field_validator("teacher_id")
    @classmethod
    def validate_teacher_id_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_teacher_id(v):
            raise ValueError("Invalid teacher ID format")
        return v


class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(UserInDBBase):
    """User response model without sensitive data."""
    pass


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str
