from locust import HttpUser, task, between
import json
import random
from datetime import datetime, timedelta

class ESGReportingUser(HttpUser):
    """Simulate ESG reporting user behavior for load testing"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Setup tasks performed when user starts"""
        self.auth_headers = {
            "Authorization": "Bearer test_token_" + str(random.randint(1000, 9999)),
            "Content-Type": "application/json"
        }
        self.company_id = random.randint(1, 100)
        self.created_reports = []
    
    @task(3)
    def view_dashboard(self):
        """High frequency task - view ESG dashboard"""
        with self.client.get(
            "/api/esg/dashboard/overview",
            params={
                "company_id": self.company_id,
                "time_period": random.choice(["3m", "6m", "12m"])
            },
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard failed: {response.status_code}")
    
    @task(2)
    def list_reports(self):
        """Medium frequency task - list ESG reports"""
        with self.client.get(
            "/api/esg/reports",
            params={
                "company_id": self.company_id,
                "limit": 20,
                "offset": 0
            },
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List reports failed: {response.status_code}")
    
    @task(1)
    def create_report(self):
        """Low frequency task - create new ESG report"""
        framework = random.choice(["cdp", "tcfd", "eu_taxonomy"])
        
        report_data = {
            "report_name": f"Load Test {framework.upper()} Report {random.randint(1000, 9999)}",
            "framework": framework,
            "company_id": self.company_id,
            "reporting_period_start": "2024-01-01T00:00:00Z",
            "reporting_period_end": "2024-12-31T23:59:59Z",
            "report_data": self._generate_sample_data(framework)
        }
        
        with self.client.post(
            "/api/esg/reports",
            json=report_data,
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success"):
                        self.created_reports.append(result["report_id"])
                        response.success()
                    else:
                        response.failure("Report creation returned success=False")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Create report failed: {response.status_code}")
    
    @task(1)
    def generate_report_content(self):
        """Low frequency task - generate report content"""
        if self.created_reports:
            report_id = random.choice(self.created_reports)
            
            with self.client.post(
                f"/api/esg/reports/{report_id}/generate",
                json={"framework": random.choice(["cdp", "tcfd", "eu_taxonomy"])},
                headers=self.auth_headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Generate report failed: {response.status_code}")
    
    @task(1)
    def validate_report(self):
        """Low frequency task - validate report data"""
        framework = random.choice(["cdp", "tcfd", "eu_taxonomy"])
        
        validation_data = {
            "framework": framework,
            "data": self._generate_sample_data(framework)
        }
        
        with self.client.post(
            "/api/esg/validate",
            json=validation_data,
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Validation failed: {response.status_code}")
    
    @task(1)
    def view_report_detail(self):
        """Medium frequency task - view report details"""
        if self.created_reports:
            report_id = random.choice(self.created_reports)
            
            with self.client.get(
                f"/api/esg/reports/{report_id}",
                headers=self.auth_headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"View report detail failed: {response.status_code}")
    
    @task(1)
    def check_compliance_metrics(self):
        """Medium frequency task - check compliance metrics"""
        with self.client.get(
            "/api/esg/dashboard/compliance-metrics",
            params={
                "company_id": self.company_id,
                "framework": random.choice(["cdp", "tcfd", "eu_taxonomy"])
            },
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Compliance metrics failed: {response.status_code}")
    
    @task(1)
    def export_pdf(self):
        """Low frequency task - export report to PDF"""
        if self.created_reports:
            report_id = random.choice(self.created_reports)
            
            with self.client.post(
                f"/api/esg/reports/{report_id}/export/pdf",
                json={"template_config": {"company_name": f"Load Test Company {self.company_id}"}},
                headers=self.auth_headers,
                catch_response=True,
                timeout=60  # PDF generation can take time
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"PDF export failed: {response.status_code}")
    
    def _generate_sample_data(self, framework):
        """Generate sample data for different frameworks"""
        if framework == "cdp":
            return {
                "C6": {
                    "scope_1_emissions": random.uniform(1000, 5000),
                    "scope_2_emissions": random.uniform(2000, 8000),
                    "scope_3_emissions": random.uniform(500, 3000)
                },
                "C4": {
                    "reduction_target": random.uniform(30, 60),
                    "target_year": random.choice([2030, 2035, 2040])
                }
            }
        elif framework == "tcfd":
            return {
                "governance": {
                    "description": "Load test governance description"
                },
                "strategy": {
                    "description": "Load test strategy description"
                }
            }
        elif framework == "eu_taxonomy":
            return {
                "total_revenue": random.uniform(500000, 5000000),
                "total_capex": random.uniform(50000, 500000),
                "total_opex": random.uniform(25000, 250000)
            }
        
        return {}

class ESGAdminUser(HttpUser):
    """Simulate ESG admin user behavior with approval tasks"""
    
    wait_time = between(2, 8)  # Admins work more slowly/thoughtfully
    
    def on_start(self):
        self.auth_headers = {
            "Authorization": "Bearer admin_token_" + str(random.randint(1000, 9999)),
            "Content-Type": "application/json"
        }
    
    @task(5)
    def check_pending_approvals(self):
        """High frequency admin task - check pending approvals"""
        with self.client.get(
            "/api/esg/pending-approvals",
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Pending approvals check failed: {response.status_code}")
    
    @task(2)
    def view_system_analytics(self):
        """Medium frequency admin task - view system analytics"""
        with self.client.get(
            "/api/esg/dashboard/performance-analytics",
            params={"time_range": "12m"},
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Performance analytics failed: {response.status_code}")
    
    @task(1)
    def check_integration_health(self):
        """Low frequency admin task - check integration health"""
        with self.client.get(
            "/api/esg/integration-health",
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Integration health check failed: {response.status_code}")
    
    @task(1)
    def approve_reports(self):
        """Low frequency admin task - approve reports (simulation)"""
        # This would normally interact with actual pending reports
        # For load testing, we'll simulate the approval API call
        mock_report_id = random.randint(1, 1000)
        
        approval_data = {
            "approval_level": random.randint(1, 3),
            "action": random.choice(["approve", "request_changes"]),
            "comments": f"Load test approval comment {random.randint(1, 100)}"
        }
        
        with self.client.post(
            f"/api/esg/reports/{mock_report_id}/approve",
            json=approval_data,
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            # Since this is a mock report ID, we expect it might fail
            # We'll consider both success and 404 as acceptable for load testing
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Approval simulation failed: {response.status_code}")

class ESGDataSyncUser(HttpUser):
    """Simulate data synchronization and bulk operations"""
    
    wait_time = between(10, 30)  # Sync operations happen less frequently
    
    def on_start(self):
        self.auth_headers = {
            "Authorization": "Bearer sync_token_" + str(random.randint(1000, 9999)),
            "Content-Type": "application/json"
        }
    
    @task(3)
    def bulk_report_listing(self):
        """Simulate bulk data operations"""
        with self.client.get(
            "/api/esg/reports",
            params={
                "limit": 100,  # Large batch
                "offset": random.randint(0, 500)
            },
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Bulk listing failed: {response.status_code}")
    
    @task(1)
    def system_health_comprehensive(self):
        """Comprehensive system health check"""
        endpoints = [
            "/api/esg/integration-health",
            "/api/esg/frameworks",
            "/api/esg/dashboard/overview"
        ]
        
        for endpoint in endpoints:
            with self.client.get(
                endpoint,
                headers=self.auth_headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Health check {endpoint} failed: {response.status_code}")

# Custom load testing scenarios
class StressTestUser(HttpUser):
    """High-intensity stress testing user"""
    
    wait_time = between(0.1, 0.5)  # Very short wait times for stress testing
    
    def on_start(self):
        self.auth_headers = {
            "Authorization": "Bearer stress_token_" + str(random.randint(1000, 9999)),
            "Content-Type": "application/json"
        }
    
    @task
    def rapid_dashboard_requests(self):
        """Rapid dashboard requests to test caching and performance"""
        with self.client.get(
            "/api/esg/dashboard/overview",
            params={"time_period": "12m"},
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Rapid request failed: {response.status_code}")

# Test configuration and custom behavior
def create_test_users():
    """Define different user types for mixed load testing"""
    return [
        ESGReportingUser,    # 70% normal users
        ESGAdminUser,        # 20% admin users  
        ESGDataSyncUser,     # 8% data sync users
        StressTestUser       # 2% stress test users
    ]

if __name__ == "__main__":
    # Example usage:
    # locust -f tests/load_testing.py --host=http://localhost:8000
    # 
    # For different user distributions:
    # locust -f tests/load_testing.py --host=http://localhost:8000 \
    #        --users 100 --spawn-rate 5 --run-time 300s
    pass
