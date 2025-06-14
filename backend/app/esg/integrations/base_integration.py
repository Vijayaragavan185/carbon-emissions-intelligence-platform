from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import requests
import json
import logging
from datetime import datetime
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class BaseESGIntegration(ABC):
    """Base class for all ESG platform integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url")
        self.api_key = config.get("api_key")
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST", "PUT"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        headers: Dict = None
    ) -> Dict:
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            # Default headers
            request_headers = {
                "Content-Type": "application/json",
                "User-Agent": "Carbon-Emissions-Intelligence-Platform/1.0"
            }
            
            if headers:
                request_headers.update(headers)
                
            # Add authentication
            auth_headers = self._get_auth_headers()
            if auth_headers:
                request_headers.update(auth_headers)
            
            logger.info(f"Making {method} request to {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            else:
                return {"status": "success", "message": "Request completed"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise IntegrationError(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            raise IntegrationError(f"Invalid JSON response: {str(e)}")
    
    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for the platform"""
        pass
    
    @abstractmethod
    def submit_report(self, report_data: Dict) -> Dict:
        """Submit ESG report to the platform"""
        pass
    
    @abstractmethod
    def get_submission_status(self, submission_id: str) -> Dict:
        """Get status of submitted report"""
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict) -> Dict:
        """Validate data before submission"""
        pass

class IntegrationError(Exception):
    """Custom exception for integration errors"""
    pass
