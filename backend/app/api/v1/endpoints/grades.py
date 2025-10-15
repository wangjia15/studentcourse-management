from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.grade import Grade, GradeCreate, GradeUpdate

router = APIRouter()


@router.get("/", response_model=list[Grade])
async def read_grades(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of grades."""
    # TODO: Implement grade service and endpoints
    return []


@router.get("/{grade_id}", response_model=Grade)
async def read_grade(grade_id: int, db: Session = Depends(get_db)):
    """Get grade by ID."""
    # TODO: Implement grade service and endpoints
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/", response_model=Grade)
async def create_grade(grade: GradeCreate, db: Session = Depends(get_db)):
    """Create new grade."""
    # TODO: Implement grade service and endpoints
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{grade_id}", response_model=Grade)
async def update_grade(
    grade_id: int, grade_update: GradeUpdate, db: Session = Depends(get_db)
):
    """Update grade."""
    # TODO: Implement grade service and endpoints
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{grade_id}")
async def delete_grade(grade_id: int, db: Session = Depends(get_db)):
    """Delete grade."""
    # TODO: Implement grade service and endpoints
    raise HTTPException(status_code=501, detail="Not implemented yet")
