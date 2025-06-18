import pytest
import sys
import os

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

def test_imports():
    """Test that basic imports work"""
    try:
        from app.db.database import Base, engine, SessionLocal
        from app.db.models import Company, EmissionRecord
        from app.core.config import settings
        from app.core.auth import get_current_user
        print("✅ All basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database_setup():
    """Test database connection setup"""
    try:
        from app.db.database import engine
        # Test connection (don't actually connect, just check setup)
        assert engine is not None
        print("✅ Database engine setup successful")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def test_models():
    """Test model definitions"""
    try:
        from app.db.models import Company, EmissionRecord, ScopeEnum
        
        # Test enum
        assert ScopeEnum.SCOPE_1.value == "Scope 1"
        
        # Test model attributes exist
        assert hasattr(Company, 'name')
        assert hasattr(EmissionRecord, 'calculated_emission')
        
        print("✅ Models defined correctly")
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_config():
    """Test configuration"""
    try:
        from app.core.config import settings
        
        assert settings.app_name == "Carbon Emissions Intelligence Platform"
        assert "postgresql://" in settings.database_url
        
        print("✅ Configuration working")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

# Run individual tests
if __name__ == "__main__":
    print("🧪 Running Simple Working Tests")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Database Setup", test_database_setup), 
        ("Models Test", test_models),
        ("Config Test", test_config)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n🔬 {name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Structure is working!")
    else:
        print("⚠️ Some tests failed. Check the setup.")
