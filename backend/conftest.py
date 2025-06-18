import pytest
import sys
import os
from unittest.mock import Mock

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

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
