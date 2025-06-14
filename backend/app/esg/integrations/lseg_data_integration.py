from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from .base_integration import BaseESGIntegration, IntegrationError
import logging

logger = logging.getLogger(__name__)

class LSEGDataIntegration(BaseESGIntegration):
    """LSEG (London Stock Exchange Group) ESG Data Integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.access_token = None
        self.token_expires_at = None
        
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get LSEG authentication headers"""
        if not self.access_token or self._token_expired():
            self._refresh_token()
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _token_expired(self) -> bool:
        """Check if access token is expired"""
        if not self.token_expires_at:
            return True
        return datetime.utcnow() >= self.token_expires_at
    
    def _refresh_token(self):
        """Refresh LSEG access token"""
        try:
            auth_endpoint = "auth/oauth2/v1/token"
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "trapi.esg.data.read"
            }
            
            response = self._make_request(
                method="POST",
                endpoint=auth_endpoint,
                data=auth_data
            )
            
            self.access_token = response.get("access_token")
            expires_in = response.get("expires_in", 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
            
            logger.info("LSEG access token refreshed successfully")
            
        except Exception as e:
            logger.error(f"LSEG token refresh failed: {str(e)}")
            raise IntegrationError(f"Authentication failed: {str(e)}")
    
    def submit_report(self, report_data: Dict) -> Dict:
        """LSEG is primarily a data provider, not for submitting reports"""
        return {
            "success": False,
            "message": "LSEG is a data provider - use get_esg_data() instead"
        }
    
    def get_submission_status(self, submission_id: str) -> Dict:
        """Not applicable for LSEG data provider"""
        return {"message": "Not applicable for data provider"}
    
    def validate_data(self, data: Dict) -> Dict:
        """Validate instrument identifiers for LSEG queries"""
        errors = []
        
        if not data.get("instruments"):
            errors.append("No instruments specified for LSEG query")
        
        instruments = data.get("instruments", [])
        for instrument in instruments:
            if not isinstance(instrument, str) or len(instrument) < 3:
                errors.append(f"Invalid instrument identifier: {instrument}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def get_esg_data(self, instruments: List[str], data_type: str = "scores") -> Dict:
        """Get ESG data from LSEG for specified instruments"""
        try:
            # Validate instruments
            validation = self.validate_data({"instruments": instruments})
            if not validation["valid"]:
                raise IntegrationError(f"Invalid instruments: {validation['errors']}")
            
            # Build endpoint based on data type
            if data_type == "scores":
                endpoint = "data/environmental-social-governance/v2/views/scores-full"
            elif data_type == "measures":
                endpoint = "data/environmental-social-governance/v2/views/measures-standard"
            else:
                endpoint = "data/environmental-social-governance/v2/views/basic"
            
            # Prepare parameters
            params = {
                "universe": ",".join(instruments),
                "start": "-5",  # Last 5 periods
                "end": "0",     # Current period
                "format": "json"
            }
            
            response = self._make_request(
                method="GET",
                endpoint=endpoint,
                params=params
            )
            
            # Transform response to standardized format
            return self._transform_lseg_response(response, data_type)
            
        except Exception as e:
            logger.error(f"LSEG ESG data retrieval failed: {str(e)}")
            return {"error": str(e)}
    
    def _transform_lseg_response(self, response: Dict, data_type: str) -> Dict:
        """Transform LSEG response to standardized format"""
        try:
            headers = response.get("headers", [])
            data = response.get("data", [])
            
            if not headers or not data:
                return {"error": "Empty response from LSEG"}
            
            # Extract column names
            columns = [header.get("title", "") for header in headers]
            
            # Transform data rows
            transformed_data = []
            for row in data:
                if len(row) == len(columns):
                    row_dict = dict(zip(columns, row))
                    
                    # Standardize the data structure
                    standardized_row = {
                        "instrument": row_dict.get("Instrument", ""),
                        "period_end_date": row_dict.get("Period End Date", ""),
                        "esg_combined_score": self._safe_float(row_dict.get("ESG Combined Score")),
                        "environmental_score": self._safe_float(row_dict.get("Environmental Pillar Score")),
                        "social_score": self._safe_float(row_dict.get("Social Pillar Score")),
                        "governance_score": self._safe_float(row_dict.get("Governance Pillar Score")),
                        "esg_score": self._safe_float(row_dict.get("ESG Score")),
                        "last_update_date": row_dict.get("ESG Period Last Update Date", "")
                    }
                    
                    # Add measures if available
                    if data_type == "measures":
                        standardized_row.update({
                            "co2_emissions_total": self._safe_float(row_dict.get("CO2 Equivalent Emissions Total")),
                            "women_managers": self._safe_float(row_dict.get("Women Managers")),
                            "avg_training_hours": self._safe_float(row_dict.get("Average Training Hours"))
                        })
                    
                    transformed_data.append(standardized_row)
            
            return {
                "success": True,
                "data_type": data_type,
                "instruments_count": len(transformed_data),
                "data": transformed_data,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LSEG response transformation failed: {str(e)}")
            return {"error": f"Data transformation failed: {str(e)}"}
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_industry_benchmarks(self, industry_code: str) -> Dict:
        """Get industry ESG benchmarks from LSEG"""
        try:
            endpoint = "data/environmental-social-governance/v2/industry-benchmarks"
            params = {
                "industry": industry_code,
                "metric_type": "scores"
            }
            
            response = self._make_request(
                method="GET",
                endpoint=endpoint,
                params=params
            )
            
            return response
            
        except Exception as e:
            logger.error(f"LSEG industry benchmarks retrieval failed: {str(e)}")
            return {"error": str(e)}
