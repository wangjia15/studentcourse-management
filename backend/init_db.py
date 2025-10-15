"""
Database initialization script for creating initial admin user and sample data.
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, SessionLocal
from app.models.base import Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.core.config import settings


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def create_admin_user():
    """Create default admin user."""
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if admin_user:
            print(f"Admin user {settings.ADMIN_EMAIL} already exists!")
            return
        
        # Create admin user
        admin = User(
            email=settings.ADMIN_EMAIL,
            username="admin",
            full_name="System Administrator",
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True,
            teacher_id="ADMIN001"
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"Admin user created: {admin.email}")
        print(f"Default password: {settings.ADMIN_PASSWORD}")
        print("Please change the password after first login!")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Initialize database with tables and admin user."""
    print("Initializing database...")
    create_tables()
    create_admin_user()
    print("Database initialization completed!")


if __name__ == "__main__":
    main()
