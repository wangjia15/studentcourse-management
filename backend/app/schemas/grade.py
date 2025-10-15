from pydantic import BaseModel, Field


class GradeBase(BaseModel):
    score: float = Field(..., ge=0)
    grade_letter: str | None = None
    grade_type: str
    max_score: float = Field(default=100.0, gt=0)
    weight: float = Field(default=1.0, gt=0)
    comments: str | None = None


class GradeCreate(GradeBase):
    student_id: int
    course_id: int


class GradeUpdate(BaseModel):
    score: float | None = Field(None, ge=0)
    grade_letter: str | None = None
    grade_type: str | None = None
    max_score: float | None = Field(None, gt=0)
    weight: float | None = Field(None, gt=0)
    comments: str | None = None


class Grade(GradeBase):
    id: int
    student_id: int
    course_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
