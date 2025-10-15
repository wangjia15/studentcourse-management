#!/usr/bin/env python3
"""
Database test script for Chinese University Grade Management System
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import Base
from app.db.database import engine

def test_database_creation():
    """Test database creation"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Test connection
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            # Execute a simple query
            result = db.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in result]
            print(f"✅ Database connection successful! Tables created: {tables}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        raise

if __name__ == "__main__":
    test_database_creation()
