import pytest
import sys
import os
from unittest.mock import Mock

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Import ESG modules
try:
    from app.esg.compliance.cdp import CDPReportGenerator
    from app.esg.compliance.tcfd import TCFDReportGenerator
    print("✅ Successfully imported ESG compliance modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    pytest.skip(f"Cannot import ESG modules: {e}")

class TestWorkingCompliance:
    """Working compliance tests"""
    
    @pytest.fixture
    def sample_company_data(self):
        return {
            "id": 1,
            "name": "Test Corp",
            "industry_sector": "Technology",
            "governance_structure": "Standard corporate governance"
        }
    
    @pytest.fixture
    def sample_emission_data(self):
        return [
            {
                "scope": "SCOPE_1",
                "activity_type": "Natural Gas",
                "calculated_emission": 1500.0,
                "reporting_period_start": "2024-01-01",
                "reporting_period_end": "2024-12-31"
            },
            {
                "scope": "SCOPE_2", 
                "activity_type": "Electricity",
                "calculated_emission": 2300.0,
                "reporting_period_start": "2024-01-01",
                "reporting_period_end": "2024-12-31"
            }
        ]
    
    def test_cdp_basic_generation(self, sample_company_data, sample_emission_data):
        """Test basic CDP report generation"""
        generator = CDPReportGenerator()
        
        report = generator.generate_report(sample_company_data, sample_emission_data)
        
        # Basic structure checks
        assert isinstance(report, dict)
        assert "metadata" in report
        assert "sections" in report
        assert "compliance_score" in report
        
        print(f"✅ CDP Report generated with score: {report['compliance_score']}%")
    
    def test_tcfd_basic_generation(self, sample_company_data, sample_emission_data):
        """Test basic TCFD report generation"""
        generator = TCFDReportGenerator()
        
        report = generator.generate_report(sample_company_data, sample_emission_data)
        
        # Basic structure checks
        assert isinstance(report, dict)
        assert "metadata" in report
        assert "pillars" in report
        assert "compliance_score" in report
        
        print(f"✅ TCFD Report generated with score: {report['compliance_score']}%")
    
    def test_report_data_structure(self, sample_company_data, sample_emission_data):
        """Test report data structure consistency"""
        cdp_generator = CDPReportGenerator()
        tcfd_generator = TCFDReportGenerator()
        
        cdp_report = cdp_generator.generate_report(sample_company_data, sample_emission_data)
        tcfd_report = tcfd_generator.generate_report(sample_company_data, sample_emission_data)
        
        # Both should have consistent metadata structure
        assert cdp_report["metadata"]["company_id"] == tcfd_report["metadata"]["company_id"]
        assert "framework" in cdp_report["metadata"]
        assert "framework" in tcfd_report["metadata"]
        
        print("✅ Report data structures are consistent")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
