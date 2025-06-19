#!/usr/bin/env python3
"""Debug import issues"""

import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def debug_imports():
    """Debug what's going wrong with imports"""
    print("🔍 Debugging Import Issues")
    print("=" * 60)
    
    print(f"📁 Backend directory: {backend_dir}")
    print(f"🐍 Python path: {sys.path[0]}")
    
    # Check file existence
    files_to_check = [
        "app/__init__.py",
        "app/db/__init__.py", 
        "app/db/models.py",
        "app/db/models/__init__.py",
        "app/core/config.py",
        "tests/conftest.py"
    ]
    
    print("\n📋 File Existence Check:")
    for file_path in files_to_check:
        full_path = os.path.join(backend_dir, file_path)
        status = "✅" if os.path.exists(full_path) else "❌"
        print(f"{status} {file_path}")
    
    # Try imports one by one
    print("\n🔧 Import Tests:")
    
    # Test 1: Basic app import
    try:
        import app
        print("✅ import app")
    except Exception as e:
        print(f"❌ import app - {e}")
    
    # Test 2: Database import
    try:
        from app.db.database import Base
        print("✅ from app.db.database import Base")
    except Exception as e:
        print(f"❌ from app.db.database import Base - {e}")
    
    # Test 3: Models import
    try:
        from app.db.models import ScopeEnum
        print("✅ from app.db.models import ScopeEnum")
    except Exception as e:
        print(f"❌ from app.db.models import ScopeEnum - {e}")
    
    # Test 4: Config import
    try:
        from app.core.config import settings
        print("✅ from app.core.config import settings")
    except Exception as e:
        print(f"❌ from app.core.config import settings - {e}")

if __name__ == "__main__":
    debug_imports()
