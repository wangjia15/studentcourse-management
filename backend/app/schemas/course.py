from pydantic import BaseModel


class CourseBase(BaseModel):
    course_code: str
    course_name: str
    description: str | None = None
    credits: int = 3
    semester: str


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    course_code: str | None = None
    course_name: str | None = None
    description: str | None = None
    credits: int | None = None
    semester: str | None = None


class Course(CourseBase):
    id: int
    teacher_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
