from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_current_verified_user,
    require_admin,
    require_teacher_or_admin,
)
from app.core.config import settings
from app.models.user import UserRole, User as UserModel
from app.schemas.user import UserResponse, UserUpdate, UserCreate
from app.services.permissions import Permission, PermissionService
from app.services.user import UserService
from app.db.database import get_db

router = APIRouter()
user_service = UserService()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserModel = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile."""
    # Users can only update their own profile
    if not PermissionService.check_resource_access(
        current_user.role,
        current_user.id,
        Permission.UPDATE_OWN_PROFILE,
        current_user.id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update profile",
        )

    # Users cannot change their role or activation status
    if user_update.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change role",
        )

    if user_update.is_active is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change activation status",
        )

    updated_user = user_service.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return updated_user


@router.get("/permissions")
async def get_user_permissions(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get current user's permissions."""
    permissions = PermissionService.get_user_permissions(current_user.role)
    accessible_resources = PermissionService.get_accessible_resources(
        current_user.role, "all"
    )

    return {
        "role": current_user.role.value,
        "permissions": permissions,
        "accessible_resources": accessible_resources,
    }


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None),
    current_user: UserModel = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db),
):
    """Get list of users."""
    # Check permissions
    if not PermissionService.check_permission(current_user.role, Permission.READ_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    if role:
        try:
            user_role = UserRole(role)
            users = user_service.get_users_by_role(db, user_role.value, skip, limit)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )
    else:
        users = user_service.get_users(db, skip, limit)

    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get user by ID."""
    # Check permissions
    if not PermissionService.check_permission(current_user.role, Permission.READ_USERS):
        # Users can only view their own profile
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

    user = user_service.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new user (admin only)."""
    # Check permissions
    if not PermissionService.check_permission(current_user.role, Permission.CREATE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    # Check if user already exists
    existing_user = user_service.get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    existing_username = user_service.get_user_by_username(db, username=user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user = user_service.create_user(db, user_data)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update user."""
    # Check permissions
    if not PermissionService.check_resource_access(
        current_user.role,
        current_user.id,
        Permission.UPDATE_USERS,
        user_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    # Only admins can change roles and activation status
    if current_user.role != UserRole.ADMIN:
        if user_update.role is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change roles",
            )
        if user_update.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change activation status",
            )

    updated_user = user_service.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete user (admin only)."""
    # Check permissions
    if not PermissionService.check_permission(current_user.role, Permission.DELETE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    # Prevent self-deletion
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "User deleted successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate user account (admin only)."""
    # Check permissions
    if not PermissionService.check_permission(current_user.role, Permission.ACTIVATE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    success = user_service.activate_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Deactivate user account (admin only)."""
    # Check permissions
    if not PermissionService.check_permission(current_user.role, Permission.DEACTIVATE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    # Prevent self-deactivation
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    success = user_service.deactivate_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "User deactivated successfully"}
