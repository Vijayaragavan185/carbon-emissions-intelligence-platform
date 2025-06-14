from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from .base_integration import BaseESGIntegration, IntegrationError
import logging

logger = logging.getLogger(__name__)

class EDCIIntegration(BaseESGIntegration):
    """EDCI (ESG Data Convergence Initiative) Integration for Private Equity"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.firm_id = config.get("firm_id")
        self.reporting_year = config.get("reporting_year", datetime.now().year)
        
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get EDCI API authentication headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "EDCI-Firm-ID": str(self.firm_id),
            "Content-Type": "application/json"
        }
    
    def submit_report(self, report_data: Dict) -> Dict:
        """Submit data to EDCI platform"""
        try:
            # Transform to EDCI format
            edci_data = self._transform_to_edci_format(report_data)
            
            # Validate against EDCI metrics
            validation_result = self.validate_data(edci_data)
            if not validation_result.get("valid", False):
                raise IntegrationError(f"EDCI validation failed: {validation_result.get('errors')}")
            
            # Submit to EDCI API
            endpoint = f"firms/{self.firm_id}/submissions/{self.reporting_year}"
            
            response = self._make_request(
                method="POST",
                endpoint=endpoint,
                data=edci_data
            )
            
            submission_id = response.get("submission_id")
            
            return {
                "success": True,
                "submission_id": submission_id,
                "platform": "EDCI",
                "firm_id": self.firm_id,
                "reporting_year": self.reporting_year,
                "metrics_submitted": len(edci_data.get("metrics", [])),
                "submission_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"EDCI submission failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "platform": "EDCI"
            }
    
    def get_submission_status(self, submission_id: str) -> Dict:
        """Get EDCI submission status"""
        try:
            endpoint = f"submissions/{submission_id}/status"
            
            response = self._make_request(
                method="GET",
                endpoint=endpoint
            )
            
            return {
                "submission_id": submission_id,
                "status": response.get("status"),
                "validation_status": response.get("validation_status"),
                "benchmark_available": response.get("benchmark_available", False),
                "last_updated": response.get("last_updated")
            }
            
        except Exception as e:
            logger.error(f"Failed to get EDCI submission status: {str(e)}")
            return {"error": str(e)}
    
    def validate_data(self, data: Dict) -> Dict:
        """Validate data against EDCI metrics"""
        try:
            validation_errors = []
            validation_warnings = []
            
            # Required EDCI metrics
            required_metrics = [
                "total_scope_1_emissions",
                "total_scope_2_emissions", 
                "total_energy_consumption",
                "renewable_energy_percentage",
                "water_consumption",
                "waste_generated",
                "employee_count",
                "board_diversity_percentage"
            ]
            
            metrics = data.get("metrics", {})
            
            for metric in required_metrics:
                if metric not in metrics:
                    validation_errors.append(f"Missing required EDCI metric: {metric}")
                elif metrics[metric] is None:
                    validation_warnings.append(f"EDCI metric {metric} is null")
            
            # Data quality checks
            if "total_scope_1_emissions" in metrics and metrics["total_scope_1_emissions"] < 0:
                validation_errors.append("Scope 1 emissions cannot be negative")
            
            if "renewable_energy_percentage" in metrics:
                if not 0 <= metrics["renewable_energy_percentage"] <= 100:
                    validation_errors.append("Renewable energy percentage must be between 0-100")
            
            return {
                "valid": len(validation_errors) == 0,
                "errors": validation_errors,
                "warnings": validation_warnings,
                "metrics_coverage": len(metrics) / len(required_metrics) * 100
            }
            
        except Exception as e:
            logger.error(f"EDCI validation failed: {str(e)}")
            return {"valid": False, "error": str(e)}
    
    def _transform_to_edci_format(self, report_data: Dict) -> Dict:
        """Transform report data to EDCI format"""
        try:
            # Extract emissions data
            emissions_data = {}
            if "emissions" in report_data:
                for record in report_data["emissions"]:
                    scope = record.get("scope", "").lower()
                    emission = record.get("calculated_emission", 0)
                    
                    if "scope_1" in scope:
                        emissions_data["total_scope_1_emissions"] = emissions_data.get("total_scope_1_emissions", 0) + emission
                    elif "scope_2" in scope:
                        emissions_data["total_scope_2_emissions"] = emissions_data.get("total_scope_2_emissions", 0) + emission
                    elif "scope_3" in scope:
                        emissions_data["total_scope_3_emissions"] = emissions_data.get("total_scope_3_emissions", 0) + emission
            
            # Build EDCI submission
            edci_data = {
                "firm_id": self.firm_id,
                "reporting_year": self.reporting_year,
                "submission_date": datetime.utcnow().isoformat(),
                "metrics": {
                    **emissions_data,
                    "total_energy_consumption": report_data.get("energy_consumption", 0),
                    "renewable_energy_percentage": report_data.get("renewable_energy_percentage", 0),
                    "water_consumption": report_data.get("water_consumption", 0),
                    "waste_generated": report_data.get("waste_generated", 0),
                    "employee_count": report_data.get("employee_count", 0),
                    "board_diversity_percentage": report_data.get("board_diversity_percentage", 0),
                    "revenue": report_data.get("revenue", 0),
                    "net_income": report_data.get("net_income", 0)
                },
                "portfolio_companies": self._extract_portfolio_data(report_data),
                "methodology": {
                    "emission_factors_source": "EPA/IPCC",
                    "reporting_standard": "GHG Protocol",
                    "verification_status": "Third-party verified"
                }
            }
            
            return edci_data
            
        except Exception as e:
            logger.error(f"EDCI data transformation failed: {str(e)}")
            raise IntegrationError(f"Data transformation failed: {str(e)}")
    
    def _extract_portfolio_data(self, report_data: Dict) -> List[Dict]:
        """Extract portfolio company data for EDCI"""
        portfolio_data = []
        
        companies = report_data.get("companies", [])
        for company in companies:
            portfolio_entry = {
                "company_name": company.get("name"),
                "industry_sector": company.get("industry_sector"),
                "country": company.get("country"),
                "metrics": {
                    "scope_1_emissions": company.get("scope_1_emissions", 0),
                    "scope_2_emissions": company.get("scope_2_emissions", 0),
                    "employee_count": company.get("employee_count", 0),
                    "revenue": company.get("revenue", 0)
                }
            }
            portfolio_data.append(portfolio_entry)
        
        return portfolio_data
    
    def get_benchmark_data(self) -> Dict:
        """Get EDCI benchmark data"""
        try:
            endpoint = f"benchmarks/{self.reporting_year}"
            params = {"firm_id": self.firm_id}
            
            response = self._make_request(
                method="GET",
                endpoint=endpoint,
                params=params
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get EDCI benchmark data: {str(e)}")
            return {"error": str(e)}
