import pytest
import sys
import os
from unittest.mock import Mock

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

@pytest.fixture(scope="session")
def mock_db_session():
    """Mock database session for testing"""
    return Mock()

@pytest.fixture
def sample_emission_data():
    """Sample emission data for tests"""
    return [
        {
            "scope": "SCOPE_1",
            "activity_type": "Natural Gas",
            "calculated_emission": 1500.0,
            "reporting_period_start": "2024-01-01",
            "reporting_period_end": "2024-12-31"
        }
    ]

@pytest.fixture
def sample_company_data():
    """Sample company data for tests"""
    return {
        "id": 1,
        "name": "Test Company",
        "industry_sector": "Technology",
        "country": "United States"
    }

# Remove problematic imports for now
# We'll add them back once the structure is fixed
