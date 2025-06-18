import pytest
import sys
import os

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

class TestBasicSetup:
    """Test basic setup and imports"""
    
    def test_imports(self):
        """Test that basic imports work"""
        try:
            from app.db.database import Base, engine, SessionLocal
            from app.db.models import Company, EmissionRecord
            from app.core.config import settings
            from app.core.auth import get_current_user
            
            # All imports successful
            assert Base is not None
            assert engine is not None
            assert SessionLocal is not None
            print("✅ All basic imports successful")
            
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_database_setup(self):
        """Test database connection setup"""
        try:
            from app.db.database import engine, SQLALCHEMY_DATABASE_URL
            
            # Test connection setup
            assert engine is not None
            assert "postgresql://" in SQLALCHEMY_DATABASE_URL
            print("✅ Database engine setup successful")
            
        except Exception as e:
            pytest.fail(f"Database setup failed: {e}")

    def test_models(self):
        """Test model definitions"""
        try:
            from app.db.models import Company, EmissionRecord, ScopeEnum
            
            # Test enum
            assert ScopeEnum.SCOPE_1.value == "Scope 1"
            assert ScopeEnum.SCOPE_2.value == "Scope 2"
            assert ScopeEnum.SCOPE_3.value == "Scope 3"
            
            # Test model attributes exist
            assert hasattr(Company, 'name')
            assert hasattr(Company, 'industry_sector')
            assert hasattr(EmissionRecord, 'calculated_emission')
            assert hasattr(EmissionRecord, 'scope')
            
            print("✅ Models defined correctly")
            
        except Exception as e:
            pytest.fail(f"Model test failed: {e}")

    def test_config(self):
        """Test configuration"""
        try:
            from app.core.config import settings
            
            assert settings.app_name == "Carbon Emissions Intelligence Platform"
            assert "postgresql://" in settings.database_url
            assert hasattr(settings, 'ESG_INTEGRATIONS')
            
            print("✅ Configuration working")
            
        except Exception as e:
            pytest.fail(f"Config test failed: {e}")

    def test_auth(self):
        """Test auth module"""
        try:
            from app.core.auth import get_current_user
            
            user = get_current_user()
            assert isinstance(user, dict)
            assert "id" in user
            assert "username" in user
            
            print("✅ Auth module working")
            
        except Exception as e:
            pytest.fail(f"Auth test failed: {e}")

def test_integration_imports():
    """Test that we can import everything together"""
    try:
        # Test combined imports
        from app.db import Company, EmissionRecord, Base, engine
        from app.core import settings
        
        assert Company is not None
        assert EmissionRecord is not None
        assert Base is not None
        assert engine is not None
        assert settings is not None
        
        print("✅ Integration imports successful")
        
    except ImportError as e:
        pytest.fail(f"Integration import failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
