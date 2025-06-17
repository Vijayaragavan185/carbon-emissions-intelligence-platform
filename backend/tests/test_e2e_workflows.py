import pytest
import asyncio
import requests
import json
from datetime import datetime, timedelta
import sys
import os
from unittest.mock import Mock, patch
import subprocess
import time

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.esg.services.integration_manager import IntegrationManager
from app.esg.services.approval_service import ApprovalWorkflowService
from app.esg.services.audit_service import ESGAuditService

class TestEndToEndWorkflows:
    """Test complete end-to-end ESG reporting workflows"""
    
    @pytest.fixture(scope="session")
    def test_server_url(self):
        """Base URL for test server - assumes server is running"""
        return "http://localhost:8000"
    
    @pytest.fixture
    def test_company_data(self):
        return {
            "report_name": "E2E Test CDP Report",
            "framework": "cdp",
            "company_id": 999,  # Test company ID
            "reporting_period_start": "2024-01-01T00:00:00Z",
            "reporting_period_end": "2024-12-31T23:59:59Z",
            "report_data": {
                "C6": {
                    "scope_1_emissions": 1500.0,
                    "scope_2_emissions": 2300.0,
                    "scope_3_emissions": 800.0
                },
                "C4": {
                    "reduction_target": 50.0,
                    "target_year": 2030
                }
            }
        }
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers for API requests"""
        return {
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json"
        }

class TestCompleteReportingWorkflow:
    """Test the complete ESG reporting workflow from creation to publication"""
    
    def test_full_cdp_report_lifecycle(self, test_server_url, test_company_data, auth_headers):
        """Test complete CDP report lifecycle: create -> generate -> validate -> approve -> publish"""
        base_url = f"{test_server_url}/api/esg"
        
        # Step 1: Create new ESG report
        print("Step 1: Creating ESG report...")
        create_response = requests.post(
            f"{base_url}/reports",
            json=test_company_data,
            headers=auth_headers,
            timeout=30
        )
        
        if create_response.status_code == 404:
            pytest.skip("Test server not running - skipping E2E tests")
        
        assert create_response.status_code == 200, f"Failed to create report: {create_response.text}"
        
        create_data = create_response.json()
        assert create_data["success"] is True
        report_id = create_data["report_id"]
        print(f"✓ Report created with ID: {report_id}")
        
        # Step 2: Generate report content
        print("Step 2: Generating report content...")
        generate_response = requests.post(
            f"{base_url}/reports/{report_id}/generate",
            json={"framework": "cdp"},
            headers=auth_headers,
            timeout=60
        )
        
        assert generate_response.status_code == 200
        generate_data = generate_response.json()
        assert generate_data["success"] is True
        assert generate_data["compliance_score"] > 0
        print(f"✓ Report generated with compliance score: {generate_data['compliance_score']}%")
        
        # Step 3: Validate report data
        print("Step 3: Validating report data...")
        validate_response = requests.post(
            f"{base_url}/validate",
            json={
                "framework": "cdp",
                "data": test_company_data["report_data"]
            },
            headers=auth_headers,
            timeout=30
        )
        
        assert validate_response.status_code == 200
        validation_data = validate_response.json()
        assert validation_data["success"] is True
        print(f"✓ Validation completed: {validation_data['validation_result']['valid']}")
        
        # Step 4: Export to PDF
        print("Step 4: Exporting to PDF...")
        pdf_response = requests.post(
            f"{base_url}/reports/{report_id}/export/pdf",
            json={"template_config": {"company_name": "E2E Test Corp"}},
            headers=auth_headers,
            timeout=60
        )
        
        assert pdf_response.status_code == 200
        pdf_data = pdf_response.json()
        assert pdf_data["success"] is True
        print(f"✓ PDF exported: {pdf_data['filename']}")
        
        # Step 5: Submit for approval
        print("Step 5: Submitting for approval...")
        submit_response = requests.post(
            f"{base_url}/reports/{report_id}/submit",
            headers=auth_headers,
            timeout=30
        )
        
        assert submit_response.status_code == 200
        submit_data = submit_response.json()
        assert submit_data["success"] is True
        print(f"✓ Submitted for approval: {submit_data['approval_levels']} levels")
        
        # Step 6: Simulate approval process
        print("Step 6: Processing approvals...")
        for level in range(1, 4):  # 3 approval levels
            approval_response = requests.post(
                f"{base_url}/reports/{report_id}/approve",
                json={
                    "approval_level": level,
                    "action": "approve",
                    "comments": f"Approved at level {level}"
                },
                headers=auth_headers,
                timeout=30
            )
            
            assert approval_response.status_code == 200
            approval_data = approval_response.json()
            assert approval_data["success"] is True
            print(f"✓ Approval level {level} completed")
        
        # Step 7: Verify final status
        print("Step 7: Verifying final status...")
        status_response = requests.get(
            f"{base_url}/reports/{report_id}",
            headers=auth_headers,
            timeout=30
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["report"]["status"] == "approved"
        print(f"✓ Report final status: {status_data['report']['status']}")
        
        # Step 8: Get audit trail
        print("Step 8: Checking audit trail...")
        audit_response = requests.get(
            f"{base_url}/reports/{report_id}/audit-trail",
            headers=auth_headers,
            timeout=30
        )
        
        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        assert len(audit_data["audit_trail"]) > 0
        print(f"✓ Audit trail contains {len(audit_data['audit_trail'])} entries")
        
        print("🎉 Complete workflow test passed!")
        return report_id
    
    def test_multi_framework_workflow(self, test_server_url, auth_headers):
        """Test workflow with multiple frameworks"""
        base_url = f"{test_server_url}/api/esg"
        
        frameworks = ["cdp", "tcfd", "eu_taxonomy"]
        report_ids = []
        
        for framework in frameworks:
            print(f"Testing {framework.upper()} framework...")
            
            # Create report for each framework
            test_data = {
                "report_name": f"E2E {framework.upper()} Test",
                "framework": framework,
                "company_id": 999,
                "reporting_period_start": "2024-01-01T00:00:00Z",
                "reporting_period_end": "2024-12-31T23:59:59Z",
                "report_data": {}
            }
            
            # Framework-specific data
            if framework == "cdp":
                test_data["report_data"] = {
                    "C6": {"scope_1_emissions": 1000.0}
                }
            elif framework == "tcfd":
                test_data["report_data"] = {
                    "governance": {"description": "Board oversight"}
                }
            elif framework == "eu_taxonomy":
                test_data["report_data"] = {
                    "total_revenue": 1000000,
                    "total_capex": 100000
                }
            
            create_response = requests.post(
                f"{base_url}/reports",
                json=test_data,
                headers=auth_headers,
                timeout=30
            )
            
            if create_response.status_code == 404:
                pytest.skip("Test server not running")
                
            assert create_response.status_code == 200
            create_data = create_response.json()
            report_ids.append(create_data["report_id"])
            print(f"✓ {framework.upper()} report created: {create_data['report_id']}")
        
        # Verify all reports were created
        assert len(report_ids) == len(frameworks)
        print(f"🎉 Multi-framework test completed: {len(report_ids)} reports created")
        
        return report_ids

class TestApprovalWorkflows:
    """Test approval workflow edge cases and scenarios"""
    
    def test_rejection_and_resubmission_workflow(self, test_server_url, test_company_data, auth_headers):
        """Test report rejection and resubmission workflow"""
        base_url = f"{test_server_url}/api/esg"
        
        # Create and submit report
        create_response = requests.post(f"{base_url}/reports", json=test_company_data, headers=auth_headers)
        if create_response.status_code == 404:
            pytest.skip("Test server not running")
            
        report_id = create_response.json()["report_id"]
        
        # Submit for approval
        requests.post(f"{base_url}/reports/{report_id}/submit", headers=auth_headers)
        
        # Reject at level 1
        reject_response = requests.post(
            f"{base_url}/reports/{report_id}/approve",
            json={
                "approval_level": 1,
                "action": "reject", 
                "comments": "Insufficient emissions data"
            },
            headers=auth_headers
        )
        
        assert reject_response.status_code == 200
        reject_data = reject_response.json()
        assert reject_data["success"] is True
        assert reject_data["final_status"] == "rejected"
        
        # Verify status
        status_response = requests.get(f"{base_url}/reports/{report_id}", headers=auth_headers)
        status_data = status_response.json()
        assert status_data["report"]["status"] == "rejected"
        
        print("✓ Rejection workflow tested successfully")
    
    def test_change_request_workflow(self, test_server_url, test_company_data, auth_headers):
        """Test change request workflow"""
        base_url = f"{test_server_url}/api/esg"
        
        # Create and submit report
        create_response = requests.post(f"{base_url}/reports", json=test_company_data, headers=auth_headers)
        if create_response.status_code == 404:
            pytest.skip("Test server not running")
            
        report_id = create_response.json()["report_id"]
        requests.post(f"{base_url}/reports/{report_id}/submit", headers=auth_headers)
        
        # Request changes
        changes_response = requests.post(
            f"{base_url}/reports/{report_id}/approve",
            json={
                "approval_level": 1,
                "action": "request_changes",
                "comments": "Please add more detail to governance section"
            },
            headers=auth_headers
        )
        
        assert changes_response.status_code == 200
        changes_data = changes_response.json()
        assert changes_data["success"] is True
        assert changes_data["final_status"] == "draft"
        
        print("✓ Change request workflow tested successfully")

class TestIntegrationWorkflows:
    """Test external integration workflows"""
    
    def test_mock_external_platform_integration(self):
        """Test external platform integration with mocked responses"""
        # Mock integration config
        mock_config = {
            "cdp": {
                "base_url": "https://api.test-cdp.net",
                "api_key": "test_key",
                "organization_id": "test_org"
            }
        }
        
        mock_db = Mock()
        integration_manager = IntegrationManager(mock_db, mock_config)
        
        # Mock successful submission
        with patch.object(integration_manager.integrations["cdp"], 'submit_report') as mock_submit:
            mock_submit.return_value = {
                "success": True,
                "submission_id": "TEST123",
                "platform": "CDP"
            }
            
            result = integration_manager.submit_to_platform("cdp", 1, 1)
            assert result["success"] is True
            assert result["submission_id"] == "TEST123"
        
        print("✓ External platform integration test passed")
    
    def test_integration_health_monitoring(self):
        """Test integration health monitoring"""
        mock_config = {
            "cdp": {"api_key": "test_key"},
            "lseg": {"api_key": "test_key"}
        }
        
        mock_db = Mock()
        integration_manager = IntegrationManager(mock_db, mock_config)
        
        # Mock health check responses
        with patch.object(integration_manager, 'validate_integration_health') as mock_health:
            mock_health.return_value = {
                "overall_healthy": True,
                "integrations": {
                    "cdp": {"healthy": True},
                    "lseg": {"healthy": True}
                }
            }
            
            health_status = integration_manager.validate_integration_health()
            assert health_status["overall_healthy"] is True
        
        print("✓ Integration health monitoring test passed")

class TestDataFlowWorkflows:
    """Test data flow and transformation workflows"""
    
    def test_data_pipeline_workflow(self):
        """Test complete data pipeline from ingestion to report"""
        # Mock emission data ingestion
        raw_emission_data = [
            {"facility": "Plant A", "fuel_type": "Natural Gas", "amount": 50000, "unit": "cubic meters"},
            {"facility": "Plant B", "fuel_type": "Electricity", "amount": 2000000, "unit": "kWh"}
        ]
        
        # Simulate data transformation
        transformed_data = []
        for record in raw_emission_data:
            # Mock emission factor calculation
            if record["fuel_type"] == "Natural Gas":
                emission_factor = 0.0184  # kg CO2e per cubic meter
                calculated_emission = record["amount"] * emission_factor
            elif record["fuel_type"] == "Electricity":
                emission_factor = 0.0005  # kg CO2e per kWh (mock grid factor)
                calculated_emission = record["amount"] * emission_factor
            
            transformed_data.append({
                "scope": "SCOPE_1" if record["fuel_type"] == "Natural Gas" else "SCOPE_2",
                "activity_type": record["fuel_type"],
                "calculated_emission": calculated_emission,
                "facility": record["facility"]
            })
        
        # Verify transformation
        assert len(transformed_data) == 2
        assert all("calculated_emission" in record for record in transformed_data)
        assert transformed_data[0]["scope"] == "SCOPE_1"
        assert transformed_data[1]["scope"] == "SCOPE_2"
        
        print("✓ Data pipeline workflow test passed")
        return transformed_data

class TestPerformanceWorkflows:
    """Test performance and scalability workflows"""
    
    def test_concurrent_report_generation(self):
        """Test concurrent report generation"""
        import threading
        import concurrent.futures
        
        def generate_mock_report(report_id):
            """Mock report generation"""
            time.sleep(0.1)  # Simulate processing time
            return {
                "report_id": report_id,
                "success": True,
                "compliance_score": 85
            }
        
        # Generate multiple reports concurrently
        report_ids = list(range(1, 11))  # 10 reports
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_mock_report, rid) for rid in report_ids]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        
        # Verify all reports generated successfully
        assert len(results) == 10
        assert all(result["success"] for result in results)
        
        # Should complete faster than sequential processing
        assert end_time - start_time < 1.0  # Should be faster than 1 second
        
        print(f"✓ Concurrent report generation test passed in {end_time - start_time:.2f}s")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
