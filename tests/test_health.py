#!/usr/bin/env python3

from app import create_app

def test_app_creation():
    app = create_app()
    print("✓ App created successfully")
    
    with app.app_context():
        from app.extensions import get_db
        db = get_db()
        print("✓ Database connection established")
        
        # Test a simple query
        result = db.execute("SELECT 1").fetchone()
        assert result[0] == 1
        print("✓ Database query successful")
        
        # Test that migrations ran
        result = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
        assert result is not None
        print("✓ Migrations ran successfully - users table exists")
        
    print("✓ All tests passed!")

if __name__ == "__main__":
    test_app_creation()