from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def get_user(self, db: Session, user_id: int) -> UserModel | None:
        """Get user by ID."""
        return db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> UserModel | None:
        """Get user by email."""
        return db.query(UserModel).filter(UserModel.email == email).first()

    def get_user_by_username(self, db: Session, username: str) -> UserModel | None:
        """Get user by username."""
        return db.query(UserModel).filter(UserModel.username == username).first()

    def get_user_by_student_id(self, db: Session, student_id: str) -> UserModel | None:
        """Get user by student ID."""
        return db.query(UserModel).filter(UserModel.student_id == student_id).first()

    def get_user_by_teacher_id(self, db: Session, teacher_id: str) -> UserModel | None:
        """Get user by teacher ID."""
        return db.query(UserModel).filter(UserModel.teacher_id == teacher_id).first()

    def get_users(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> list[UserModel]:
        """Get list of users with pagination."""
        return db.query(UserModel).offset(skip).limit(limit).all()

    def get_users_by_role(
        self, db: Session, role: str, skip: int = 0, limit: int = 100
    ) -> list[UserModel]:
        """Get users by role."""
        return (
            db.query(UserModel)
            .filter(UserModel.role == role)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_user(self, db: Session, user: UserCreate) -> UserModel:
        """Create a new user."""
        hashed_password = get_password_hash(user.password)
        db_user = UserModel(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=hashed_password,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            student_id=user.student_id,
            teacher_id=user.teacher_id,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def update_user(
        self, db: Session, user_id: int, user_update: UserUpdate
    ) -> UserModel | None:
        """Update user information."""
        db_user = self.get_user(db, user_id=user_id)
        if db_user:
            update_data = user_update.model_dump(exclude_unset=True)
            if "password" in update_data:
                update_data["hashed_password"] = get_password_hash(
                    update_data.pop("password")
                )

            for field, value in update_data.items():
                setattr(db_user, field, value)

            db.commit()
            db.refresh(db_user)
        return db_user

    def delete_user(self, db: Session, user_id: int) -> bool:
        """Delete user."""
        db_user = self.get_user(db, user_id=user_id)
        if db_user:
            db.delete(db_user)
            db.commit()
            return True
        return False

    def authenticate_user(
        self, db: Session, username: str, password: str
    ) -> UserModel | None:
        """Authenticate user with username and password."""
        user = self.get_user_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def activate_user(self, db: Session, user_id: int) -> bool:
        """Activate user account."""
        db_user = self.get_user(db, user_id=user_id)
        if db_user:
            db_user.is_active = True
            db_user.is_verified = True
            db.commit()
            return True
        return False

    def deactivate_user(self, db: Session, user_id: int) -> bool:
        """Deactivate user account."""
        db_user = self.get_user(db, user_id=user_id)
        if db_user:
            db_user.is_active = False
            db.commit()
            return True
        return False
