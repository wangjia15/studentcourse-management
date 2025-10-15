from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.course import Course, CourseCreate, CourseUpdate

router = APIRouter()


@router.get("/", response_model=list[Course])
async def read_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of courses."""
    # TODO: Implement course service and endpoints
    return []


@router.get("/{course_id}", response_model=Course)
async def read_course(course_id: int, db: Session = Depends(get_db)):
    """Get course by ID."""
    # TODO: Implement course service and endpoints
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/", response_model=Course)
async def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    """Create new course."""
    # TODO: Implement course service and endpoints
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{course_id}", response_model=Course)
async def update_course(
    course_id: int, course_update: CourseUpdate, db: Session = Depends(get_db)
):
    """Update course."""
    # TODO: Implement course service and endpoints
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{course_id}")
async def delete_course(course_id: int, db: Session = Depends(get_db)):
    """Delete course."""
    # TODO: Implement course service and endpoints
    raise HTTPException(status_code=501, detail="Not implemented yet")
