from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from .base_integration import BaseESGIntegration, IntegrationError
import logging

logger = logging.getLogger(__name__)

class CDPIntegration(BaseESGIntegration):
    """CDP (Carbon Disclosure Project) Platform Integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.organization_id = config.get("organization_id")
        self.questionnaire_type = config.get("questionnaire_type", "climate_change")
        self.disclosure_year = config.get("disclosure_year", datetime.now().year)
        
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get CDP API authentication headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "CDP-Organization-ID": str(self.organization_id)
        }
    
    def submit_report(self, report_data: Dict) -> Dict:
        """Submit CDP climate change report"""
        try:
            # Validate data first
            validation_result = self.validate_data(report_data)
            if not validation_result.get("valid", False):
                raise IntegrationError(f"Data validation failed: {validation_result.get('errors')}")
            
            # Transform data to CDP format
            cdp_formatted_data = self._transform_to_cdp_format(report_data)
            
            # Submit to CDP Disclosure API
            endpoint = f"disclosure/{self.disclosure_year}/{self.questionnaire_type}/responses"
            
            response = self._make_request(
                method="POST",
                endpoint=endpoint,
                data=cdp_formatted_data
            )
            
            submission_id = response.get("submission_id")
            
            logger.info(f"CDP report submitted successfully: {submission_id}")
            
            return {
                "success": True,
                "submission_id": submission_id,
                "platform": "CDP",
                "questionnaire_type": self.questionnaire_type,
                "submission_timestamp": datetime.utcnow().isoformat(),
                "validation_score": validation_result.get("score", 0)
            }
            
        except Exception as e:
            logger.error(f"CDP submission failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "platform": "CDP"
            }
    
    def get_submission_status(self, submission_id: str) -> Dict:
        """Get CDP submission status"""
        try:
            endpoint = f"disclosure/{self.disclosure_year}/submissions/{submission_id}/status"
            
            response = self._make_request(
                method="GET",
                endpoint=endpoint
            )
            
            return {
                "submission_id": submission_id,
                "status": response.get("status"),
                "last_updated": response.get("last_updated"),
                "completion_percentage": response.get("completion_percentage", 0),
                "validation_errors": response.get("validation_errors", []),
                "next_steps": response.get("next_steps", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get CDP submission status: {str(e)}")
            return {"error": str(e)}
    
    def validate_data(self, data: Dict) -> Dict:
        """Validate data against CDP requirements"""
        try:
            validation_errors = []
            validation_warnings = []
            score = 100
            
            # Check required sections
            required_sections = ["C1", "C2", "C4", "C6"]
            for section in required_sections:
                if section not in data.get("sections", {}):
                    validation_errors.append(f"Missing required section: {section}")
                    score -= 20
            
            # Check data completeness
            sections = data.get("sections", {})
            
            # C1 - Governance validation
            if "C1" in sections:
                c1_data = sections["C1"]
                if not c1_data.get("C1.1", {}).get("response"):
                    validation_warnings.append("C1.1 governance oversight response incomplete")
                    score -= 5
            
            # C6 - Emissions data validation
            if "C6" in sections:
                c6_data = sections["C6"]
                
                # Check Scope 1 emissions
                scope1_data = c6_data.get("C6.1", {})
                if not scope1_data.get("scope_1_emissions"):
                    validation_errors.append("Scope 1 emissions data required")
                    score -= 15
                elif scope1_data["scope_1_emissions"] <= 0:
                    validation_warnings.append("Scope 1 emissions should be positive")
                    score -= 5
                
                # Check data quality
                if not scope1_data.get("verification_status"):
                    validation_warnings.append("Third-party verification recommended")
                    score -= 5
            
            # Check methodology consistency
            if "C5" in sections:
                c5_data = sections["C5"]
                if not c5_data.get("C5.2", {}).get("standards_used"):
                    validation_warnings.append("Emission calculation standards not specified")
                    score -= 5
            
            return {
                "valid": len(validation_errors) == 0,
                "score": max(0, score),
                "errors": validation_errors,
                "warnings": validation_warnings,
                "completeness": self._calculate_completeness(data)
            }
            
        except Exception as e:
            logger.error(f"CDP validation failed: {str(e)}")
            return {
                "valid": False,
                "error": str(e),
                "score": 0
            }
    
    def _transform_to_cdp_format(self, report_data: Dict) -> Dict:
        """Transform internal report format to CDP API format"""
        try:
            cdp_data = {
                "organization_id": self.organization_id,
                "questionnaire_type": self.questionnaire_type,
                "disclosure_year": self.disclosure_year,
                "submission_timestamp": datetime.utcnow().isoformat(),
                "responses": []
            }
            
            sections = report_data.get("sections", {})
            
            for section_key, section_data in sections.items():
                for question_key, question_data in section_data.items():
                    
                    response_entry = {
                        "question_id": f"{section_key}.{question_key}",
                        "section": section_key,
                        "question": question_key,
                        "response_type": self._get_response_type(question_data),
                        "response_data": self._format_response_data(question_data)
                    }
                    
                    cdp_data["responses"].append(response_entry)
            
            return cdp_data
            
        except Exception as e:
            logger.error(f"CDP data transformation failed: {str(e)}")
            raise IntegrationError(f"Data transformation failed: {str(e)}")
    
    def _get_response_type(self, question_data: Dict) -> str:
        """Determine CDP response type"""
        if isinstance(question_data.get("response"), dict):
            return "structured"
        elif isinstance(question_data.get("response"), list):
            return "table"
        elif isinstance(question_data.get("response"), (int, float)):
            return "numeric"
        else:
            return "text"
    
    def _format_response_data(self, question_data: Dict) -> Dict:
        """Format response data for CDP API"""
        response = question_data.get("response")
        
        formatted_data = {
            "value": response,
            "unit": question_data.get("unit"),
            "methodology": question_data.get("methodology"),
            "verification_status": question_data.get("verification_status"),
            "data_quality": question_data.get("data_quality"),
            "comments": question_data.get("comments")
        }
        
        # Remove None values
        return {k: v for k, v in formatted_data.items() if v is not None}
    
    def _calculate_completeness(self, data: Dict) -> int:
        """Calculate data completeness percentage"""
        total_questions = 0
        answered_questions = 0
        
        sections = data.get("sections", {})
        for section_data in sections.values():
            for question_data in section_data.values():
                total_questions += 1
                if question_data.get("response") is not None:
                    answered_questions += 1
        
        if total_questions == 0:
            return 0
        
        return int((answered_questions / total_questions) * 100)
    
    def get_questionnaire_structure(self) -> Dict:
        """Get CDP questionnaire structure for the current year"""
        try:
            endpoint = f"questionnaires/{self.disclosure_year}/{self.questionnaire_type}/structure"
            
            response = self._make_request(
                method="GET",
                endpoint=endpoint
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get CDP questionnaire structure: {str(e)}")
            return {"error": str(e)}
    
    def get_benchmark_data(self, industry_sector: str) -> Dict:
        """Get CDP benchmark data for industry comparison"""
        try:
            endpoint = f"benchmarks/{self.disclosure_year}/{self.questionnaire_type}"
            params = {
                "industry_sector": industry_sector,
                "include_scores": True
            }
            
            response = self._make_request(
                method="GET",
                endpoint=endpoint,
                params=params
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get CDP benchmark data: {str(e)}")
            return {"error": str(e)}
