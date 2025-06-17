import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os
import json
import sys
from unittest.mock import Mock, patch, MagicMock
from reportlab.lib.pagesizes import A4

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.esg.services.pdf_generator import ESGReportPDFGenerator
from app.esg.compliance.cdp import CDPReportGenerator
from app.esg.compliance.tcfd import TCFDReportGenerator
from app.esg.compliance.eu_taxonomy import EUTaxonomyReportGenerator

class TestPDFReportGeneration:
    """Test PDF report generation functionality"""
    
    @pytest.fixture
    def sample_cdp_report_data(self):
        return {
            "metadata": {
                "framework": "CDP",
                "company_id": 1,
                "reporting_year": 2024,
                "generated_at": datetime.utcnow().isoformat()
            },
            "sections": {
                "C1": {
                    "C1.1": {
                        "question": "Is there board-level oversight of climate-related issues?",
                        "response": "Yes",
                        "details": {
                            "board_oversight": True,
                            "frequency_of_review": "Quarterly"
                        }
                    }
                },
                "C6": {
                    "C6.1": {
                        "question": "What were your organization's gross global Scope 1 emissions?",
                        "scope_1_emissions": 1500.0,
                        "methodology": "Direct measurement"
                    }
                }
            },
            "compliance_score": 85
        }
    
    @pytest.fixture
    def sample_tcfd_report_data(self):
        return {
            "metadata": {
                "framework": "TCFD",
                "company_id": 1,
                "reporting_year": 2024
            },
            "pillars": {
                "governance": {
                    "board_oversight": {
                        "recommendation": "Describe board oversight",
                        "disclosure": {
                            "oversight_structure": "Board-level Climate Committee"
                        },
                        "implementation_status": "Implemented"
                    }
                },
                "strategy": {
                    "risks_opportunities": {
                        "recommendation": "Describe climate risks and opportunities",
                        "disclosure": {
                            "physical_risks": [
                                {
                                    "risk": "Extreme weather",
                                    "time_horizon": "Short-term"
                                }
                            ]
                        },
                        "implementation_status": "Implemented"
                    }
                }
            },
            "compliance_score": 92
        }
    
    @pytest.fixture
    def sample_eu_taxonomy_data(self):
        return {
            "metadata": {
                "framework": "EU_Taxonomy",
                "company_id": 1,
                "reporting_year": 2024
            },
            "summary_kpis": {
                "turnover": {
                    "eligible_percentage": 40.0,
                    "aligned_percentage": 35.0,
                    "absolute_eligible": 400000,
                    "absolute_aligned": 350000
                },
                "capex": {
                    "eligible_percentage": 60.0,
                    "aligned_percentage": 50.0,
                    "absolute_eligible": 60000,
                    "absolute_aligned": 50000
                }
            },
            "compliance_score": 78
        }
    
    def test_cdp_pdf_generation(self, sample_cdp_report_data):
        """Test CDP PDF report generation"""
        pdf_generator = ESGReportPDFGenerator()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Generate PDF
            result_path = pdf_generator.generate_cdp_report(sample_cdp_report_data, output_path)
            
            # Verify file was created
            assert os.path.exists(result_path)
            assert result_path == output_path
            
            # Verify file is not empty
            file_size = os.path.getsize(result_path)
            assert file_size > 1000  # PDF should be at least 1KB
            
            # Verify it's a valid PDF (basic check)
            with open(result_path, 'rb') as f:
                header = f.read(8)
                assert header.startswith(b'%PDF-')
                
        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_tcfd_pdf_generation(self, sample_tcfd_report_data):
        """Test TCFD PDF report generation"""
        pdf_generator = ESGReportPDFGenerator()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            result_path = pdf_generator.generate_tcfd_report(sample_tcfd_report_data, output_path)
            
            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 1000
            
            # Verify PDF structure
            with open(result_path, 'rb') as f:
                content = f.read()
                assert b'TCFD' in content
                assert b'Governance' in content
                assert b'Strategy' in content
                
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_eu_taxonomy_pdf_generation(self, sample_eu_taxonomy_data):
        """Test EU Taxonomy PDF report generation"""
        pdf_generator = ESGReportPDFGenerator()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            result_path = pdf_generator.generate_eu_taxonomy_report(sample_eu_taxonomy_data, output_path)
            
            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 1000
            
            # Verify PDF contains taxonomy-specific content
            with open(result_path, 'rb') as f:
                content = f.read()
                assert b'EU Taxonomy' in content
                assert b'KPI' in content
                
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_pdf_generation_with_custom_branding(self, sample_cdp_report_data):
        """Test PDF generation with custom branding"""
        custom_template = {
            "company_name": "Test Company Inc.",
            "primary_color": "#FF0000",
            "logo_path": None,
            "footer_text": "Custom Footer Text"
        }
        
        pdf_generator = ESGReportPDFGenerator(custom_template)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            result_path = pdf_generator.generate_cdp_report(sample_cdp_report_data, output_path)
            assert os.path.exists(result_path)
            
            # Verify custom branding is applied
            with open(result_path, 'rb') as f:
                content = f.read()
                assert b'Test Company Inc.' in content
                assert b'Custom Footer Text' in content
                
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_pdf_generation_error_handling(self):
        """Test PDF generation error handling"""
        pdf_generator = ESGReportPDFGenerator()
        
        # Test with invalid data
        invalid_data = {"invalid": "data"}
        
        with pytest.raises(Exception):
            pdf_generator.generate_cdp_report(invalid_data, "/invalid/path/test.pdf")
    
    def test_multiple_report_formats(self, sample_cdp_report_data, sample_tcfd_report_data):
        """Test generating multiple report formats"""
        pdf_generator = ESGReportPDFGenerator()
        
        reports = [
            (sample_cdp_report_data, 'cdp'),
            (sample_tcfd_report_data, 'tcfd')
        ]
        
        generated_files = []
        
        try:
            for report_data, report_type in reports:
                with tempfile.NamedTemporaryFile(suffix=f'_{report_type}.pdf', delete=False) as tmp_file:
                    output_path = tmp_file.name
                
                if report_type == 'cdp':
                    result_path = pdf_generator.generate_cdp_report(report_data, output_path)
                elif report_type == 'tcfd':
                    result_path = pdf_generator.generate_tcfd_report(report_data, output_path)
                
                assert os.path.exists(result_path)
                assert os.path.getsize(result_path) > 1000
                generated_files.append(result_path)
                
        finally:
            # Cleanup all generated files
            for file_path in generated_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)

class TestReportDataGeneration:
    """Test report data generation and transformation"""
    
    @pytest.fixture
    def sample_company_data(self):
        return {
            "id": 1,
            "name": "Test Corporation",
            "industry_sector": "Technology",
            "country": "United States"
        }
    
    @pytest.fixture
    def sample_emission_data(self):
        return [
            {
                "scope": "SCOPE_1",
                "activity_type": "Natural Gas",
                "calculated_emission": 1200.5,
                "activity_amount": 50000,
                "activity_unit": "cubic meters"
            },
            {
                "scope": "SCOPE_2",
                "activity_type": "Electricity",
                "calculated_emission": 2500.8,
                "activity_amount": 5000000,
                "activity_unit": "kWh"
            }
        ]
    
    def test_cdp_data_transformation(self, sample_company_data, sample_emission_data):
        """Test CDP data transformation and validation"""
        generator = CDPReportGenerator()
        
        report = generator.generate_report(sample_company_data, sample_emission_data)
        
        # Test data completeness
        assert report["sections"]["C6"]["C6.1"]["scope_1_emissions"] == 1200.5
        assert report["sections"]["C6"]["C6.2"]["scope_2_emissions"] == 2500.8
        
        # Test calculated totals
        total_scope_1_2 = 1200.5 + 2500.8
        assert abs(report["sections"]["C6"]["C6.1"]["scope_1_emissions"] + 
                  report["sections"]["C6"]["C6.2"]["scope_2_emissions"] - total_scope_1_2) < 0.1
    
    def test_tcfd_risk_assessment_generation(self, sample_company_data, sample_emission_data):
        """Test TCFD risk assessment data generation"""
        generator = TCFDReportGenerator()
        
        report = generator.generate_report(sample_company_data, sample_emission_data)
        
        strategy_pillar = report["pillars"]["strategy"]
        risks_data = strategy_pillar["risks_opportunities"]["disclosure"]
        
        # Verify risk categories are present
        assert "physical_risks" in risks_data
        assert "transition_risks" in risks_data
        assert "opportunities" in risks_data
        
        # Verify risk structure
        physical_risks = risks_data["physical_risks"]
        assert "acute" in physical_risks
        assert "chronic" in physical_risks
        
        # Verify transition risks
        transition_risks = risks_data["transition_risks"]
        assert "policy_legal" in transition_risks
        assert "technology" in transition_risks
    
    def test_report_versioning_and_updates(self, sample_company_data, sample_emission_data):
        """Test report versioning when data is updated"""
        generator = CDPReportGenerator()
        
        # Generate initial report
        initial_report = generator.generate_report(sample_company_data, sample_emission_data)
        initial_score = initial_report["compliance_score"]
        
        # Update emission data
        updated_emission_data = sample_emission_data.copy()
        updated_emission_data[0]["calculated_emission"] = 1500.0  # Increase scope 1
        
        # Generate updated report
        updated_report = generator.generate_report(sample_company_data, updated_emission_data)
        updated_score = updated_report["compliance_score"]
        
        # Verify data was updated
        assert updated_report["sections"]["C6"]["C6.1"]["scope_1_emissions"] == 1500.0
        assert updated_report["sections"]["C6"]["C6.1"]["scope_1_emissions"] != initial_report["sections"]["C6"]["C6.1"]["scope_1_emissions"]
    
    def test_report_data_validation_and_sanitization(self):
        """Test report data validation and sanitization"""
        generator = CDPReportGenerator()
        
        # Test with invalid/missing data
        incomplete_company_data = {"id": 1}  # Missing required fields
        empty_emission_data = []
        
        report = generator.generate_report(incomplete_company_data, empty_emission_data)
        
        # Should still generate report but with lower compliance score
        assert "sections" in report
        assert report["compliance_score"] < 50  # Should be low due to missing data
        
        # Test with negative emission values (should be handled)
        invalid_emission_data = [
            {
                "scope": "SCOPE_1",
                "calculated_emission": -100.0,  # Invalid negative value
                "activity_type": "Test"
            }
        ]
        
        report_with_invalid = generator.generate_report(incomplete_company_data, invalid_emission_data)
        # Should handle invalid data gracefully
        assert "sections" in report_with_invalid

class TestReportExportFormats:
    """Test various report export formats"""
    
    def test_json_export(self, sample_cdp_report_data):
        """Test JSON export functionality"""
        # Convert report to JSON
        json_data = json.dumps(sample_cdp_report_data, indent=2, default=str)
        
        # Verify JSON is valid
        parsed_data = json.loads(json_data)
        assert parsed_data["metadata"]["framework"] == "CDP"
        assert parsed_data["compliance_score"] == 85
    
    def test_csv_export_capability(self, sample_cdp_report_data):
        """Test CSV export capability for emissions data"""
        # Extract emissions data for CSV export
        emissions_data = []
        
        if "C6" in sample_cdp_report_data["sections"]:
            c6_data = sample_cdp_report_data["sections"]["C6"]
            for question_key, question_data in c6_data.items():
                if "scope_1_emissions" in question_data:
                    emissions_data.append({
                        "scope": "Scope 1",
                        "emissions": question_data["scope_1_emissions"],
                        "question": question_key
                    })
        
        # Convert to DataFrame (simulating CSV export)
        df = pd.DataFrame(emissions_data)
        
        assert len(df) > 0
        assert "scope" in df.columns
        assert "emissions" in df.columns
    
    def test_xml_export_structure(self, sample_cdp_report_data):
        """Test XML export structure"""
        import xml.etree.ElementTree as ET
        
        # Create XML structure
        root = ET.Element("ESGReport")
        
        # Add metadata
        metadata = ET.SubElement(root, "metadata")
        for key, value in sample_cdp_report_data["metadata"].items():
            elem = ET.SubElement(metadata, key)
            elem.text = str(value)
        
        # Add compliance score
        score_elem = ET.SubElement(root, "compliance_score")
        score_elem.text = str(sample_cdp_report_data["compliance_score"])
        
        # Convert to string
        xml_string = ET.tostring(root, encoding='unicode')
        
        # Verify XML structure
        assert "<ESGReport>" in xml_string
        assert "<metadata>" in xml_string
        assert "<compliance_score>85</compliance_score>" in xml_string

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
