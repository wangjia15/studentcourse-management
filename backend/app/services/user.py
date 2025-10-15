from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def get_user(self, db: Session, user_id: int) -> UserModel | None:
        return db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> UserModel | None:
        return db.query(UserModel).filter(UserModel.email == email).first()

    def get_user_by_username(self, db: Session, username: str) -> UserModel | None:
        return db.query(UserModel).filter(UserModel.username == username).first()

    def get_users(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> list[UserModel]:
        return db.query(UserModel).offset(skip).limit(limit).all()

    def create_user(self, db: Session, user: UserCreate) -> UserModel:
        hashed_password = get_password_hash(user.password)
        db_user = UserModel(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=hashed_password,
            role=user.role,
            is_active=user.is_active,
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
        db_user = self.get_user(db, user_id=user_id)
        if db_user:
            update_data = user_update.dict(exclude_unset=True)
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
        db_user = self.get_user(db, user_id=user_id)
        if db_user:
            db.delete(db_user)
            db.commit()
            return True
        return False

    def authenticate_user(
        self, db: Session, username: str, password: str
    ) -> UserModel | None:
        user = self.get_user_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
