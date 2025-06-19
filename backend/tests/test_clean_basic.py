import pytest
import sys
import os

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

class TestCleanBasic:
    """Clean basic tests without complex imports"""
    
    def test_python_path(self):
        """Test that Python path is set correctly"""
        assert backend_dir in sys.path
        print(f"✅ Python path set: {backend_dir}")
    
    def test_app_package_import(self):
        """Test basic app package import"""
        try:
            import app
            assert hasattr(app, '__version__')
            print("✅ App package imports successfully")
        except ImportError as e:
            pytest.fail(f"Could not import app package: {e}")
    
    def test_database_module_import(self):
        """Test database module import"""
        try:
            from app.db.database import Base, engine, SessionLocal
            assert Base is not None
            assert engine is not None
            print("✅ Database module imports successfully")
        except ImportError as e:
            pytest.fail(f"Could not import database module: {e}")
    
    def test_config_import(self):
        """Test config import"""
        try:
            from app.core.config import settings
            assert settings.PROJECT_NAME == "Carbon Emissions Intelligence Platform"
            print("✅ Config imports successfully")
        except ImportError as e:
            pytest.fail(f"Could not import config: {e}")
    
    def test_models_basic(self):
        """Test basic model import without relationships"""
        try:
            # Import the actual models file directly
            from app.db.models import ScopeEnum
            
            # Test enum values
            assert ScopeEnum.SCOPE_1.value == "Scope 1"
            assert ScopeEnum.SCOPE_2.value == "Scope 2"
            assert ScopeEnum.SCOPE_3.value == "Scope 3"
            
            print("✅ Basic models import successfully")
        except ImportError as e:
            pytest.fail(f"Could not import models: {e}")

def test_directory_structure():
    """Test that required directories exist"""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_dirs = [
        "app",
        "app/db", 
        "app/core",
        "tests"
    ]
    
    for dir_path in required_dirs:
        full_path = os.path.join(backend_dir, dir_path)
        assert os.path.exists(full_path), f"Required directory missing: {dir_path}"
    
    print("✅ Directory structure is correct")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
