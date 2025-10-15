from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user import UserService

router = APIRouter()
user_service = UserService()


@router.get("/", response_model=list[User])
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of users."""
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID."""
    db_user = user_service.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post("/", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create new user."""
    db_user = user_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = user_service.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    return user_service.create_user(db=db, user=user)


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)
):
    """Update user."""
    db_user = user_service.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete user."""
    success = user_service.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
