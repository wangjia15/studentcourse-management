from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    role: UserRole = UserRole.STUDENT
    is_active: bool = True
    student_id: str | None = None
    teacher_id: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    student_id: str | None = None
    teacher_id: str | None = None
    password: str | None = None


class UserInDBBase(UserBase):
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str
