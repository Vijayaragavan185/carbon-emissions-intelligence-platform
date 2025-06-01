import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
from app.utils.rate_limiter import RateLimiter
from app.utils.error_handler import handle_api_error

logger = logging.getLogger(__name__)

class EPAClient:
    """EPA eGRID API client for emission factor data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.epa.gov/egrid"
        self.rate_limiter = RateLimiter(requests_per_minute=100)
        self.session = requests.Session()
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Carbon-Emissions-Platform/1.0'
        }
        if api_key:
            headers['X-API-Key'] = api_key
        
        self.session.headers.update(headers)
    
    @handle_api_error(max_retries=3)
    def get_emission_factors(self, year: int = None) -> List[Dict]:
        """Fetch emission factors from EPA eGRID"""
        self.rate_limiter.wait_if_needed()
        
        # For demo purposes, return mock data if no real API
        if not self.api_key:
            return self._get_mock_epa_data(year)
        
        url = f"{self.base_url}/emission-factors"
        params = {'year': year} if year else {}
        
        logger.info(f"Fetching EPA emission factors for year: {year}")
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return self._transform_epa_response(data)
    
    def _get_mock_epa_data(self, year: int = None) -> List[Dict]:
        """Return mock EPA data for testing"""
        current_year = year or datetime.now().year
        return [{
            'name': 'US Grid Average',
            'scope': 'Scope 2',
            'category': 'Electricity',
            'factor_value': 0.4091,
            'unit': 'kg CO2e/kWh',
            'source': 'EPA',
            'region': 'US',
            'year': current_year,
            'uncertainty': 15.0,
            'data_quality': 4.5,
            'metadata': {
                'source_id': 'epa_grid_avg',
                'methodology': 'EPA eGRID',
                'data_source': 'EPA eGRID Database'
            }
        }, {
            'name': 'Natural Gas - Stationary Combustion',
            'scope': 'Scope 1',
            'category': 'Stationary Combustion',
            'factor_value': 0.0539,
            'unit': 'kg CO2e/kWh',
            'source': 'EPA',
            'region': 'US',
            'year': current_year,
            'uncertainty': 5.0,
            'data_quality': 4.8,
            'metadata': {
                'source_id': 'epa_natgas',
                'methodology': 'EPA GHG Inventory',
                'data_source': 'EPA Emission Factors'
            }
        }]
    
    def _transform_epa_response(self, data: Dict) -> List[Dict]:
        """Transform EPA API response to standardized format"""
        factors = []
        
        for item in data.get('factors', []):
            factor = {
                'name': item.get('fuel_type', ''),
                'scope': 'Scope 2' if 'electricity' in item.get('category', '').lower() else 'Scope 1',
                'category': item.get('category', ''),
                'factor_value': float(item.get('emission_factor', 0)),
                'unit': item.get('unit', 'kg CO2e/MWh'),
                'source': 'EPA',
                'region': item.get('region', 'US'),
                'year': item.get('year', datetime.now().year),
                'uncertainty': item.get('uncertainty_percent'),
                'data_quality': self._calculate_quality_score(item),
                'metadata': {
                    'source_id': item.get('id'),
                    'methodology': item.get('methodology'),
                    'data_source': 'EPA eGRID'
                }
            }
            factors.append(factor)
        
        return factors
    
    def _calculate_quality_score(self, item: Dict) -> float:
        """Calculate data quality score (1-5)"""
        score = 5.0
        
        if not item.get('uncertainty_percent'):
            score -= 0.5
        
        year = item.get('year', datetime.now().year)
        if datetime.now().year - year > 2:
            score -= 1.0
        
        if not item.get('methodology'):
            score -= 0.5
        
        return max(1.0, score)

class DEFRAClient:
    """DEFRA UK Government emission factors API client"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.gov.uk/defra/emission-factors"
        self.rate_limiter = RateLimiter(requests_per_minute=60)
        self.session = requests.Session()
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Carbon-Emissions-Platform/1.0'
        }
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        self.session.headers.update(headers)
    
    @handle_api_error(max_retries=3)
    def get_uk_emission_factors(self, year: int = None) -> List[Dict]:
        """Fetch UK emission factors from DEFRA"""
        self.rate_limiter.wait_if_needed()
        
        # For demo purposes, return mock data if no real API
        if not self.api_key:
            return self._get_mock_defra_data(year)
        
        url = f"{self.base_url}/uk-factors"
        params = {'year': year or datetime.now().year}
        
        logger.info(f"Fetching DEFRA UK emission factors for year: {year}")
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return self._transform_defra_response(data)
    
    def _get_mock_defra_data(self, year: int = None) -> List[Dict]:
        """Return mock DEFRA data for testing"""
        current_year = year or datetime.now().year
        return [{
            'name': 'UK Grid Electricity',
            'scope': 'Scope 2',
            'category': 'Electricity',
            'factor_value': 0.21233,
            'unit': 'kg CO2e/kWh',
            'source': 'DEFRA',
            'region': 'UK',
            'year': current_year,
            'uncertainty': 8.0,
            'data_quality': 4.7,
            'metadata': {
                'source_id': 'defra_uk_elec',
                'methodology': 'DEFRA GHG Conversion Factors',
                'data_source': 'UK DEFRA'
            }
        }, {
            'name': 'Natural Gas',
            'scope': 'Scope 1',
            'category': 'Fuels',
            'factor_value': 0.18396,
            'unit': 'kg CO2e/kWh',
            'source': 'DEFRA',
            'region': 'UK',
            'year': current_year,
            'uncertainty': 2.0,
            'data_quality': 4.9,
            'metadata': {
                'source_id': 'defra_natgas',
                'methodology': 'DEFRA GHG Conversion Factors',
                'data_source': 'UK DEFRA'
            }
        }]
    
    def _transform_defra_response(self, data: Dict) -> List[Dict]:
        """Transform DEFRA API response to standardized format"""
        factors = []
        
        for item in data.get('factors', []):
            factor = {
                'name': item.get('fuel_name', ''),
                'scope': self._determine_scope(item.get('category', '')),
                'category': item.get('category', ''),
                'factor_value': float(item.get('kg_co2e_per_unit', 0)),
                'unit': item.get('unit', 'kg CO2e/unit'),
                'source': 'DEFRA',
                'region': 'UK',
                'year': item.get('year', datetime.now().year),
                'uncertainty': item.get('uncertainty'),
                'data_quality': 4.5,  # DEFRA generally has high quality
                'metadata': {
                    'source_id': item.get('id'),
                    'methodology': 'DEFRA GHG Conversion Factors',
                    'data_source': 'UK DEFRA'
                }
            }
            factors.append(factor)
        
        return factors
    
    def _determine_scope(self, category: str) -> str:
        """Determine GHG scope from category"""
        category_lower = category.lower()
        if any(word in category_lower for word in ['electricity', 'grid']):
            return 'Scope 2'
        elif any(word in category_lower for word in ['transport', 'delivery']):
            return 'Scope 3'
        else:
            return 'Scope 1'

class IPCCClient:
    """IPCC emission factors API client"""
    
    def __init__(self):
        self.base_url = "https://www.ipcc-nggip.iges.or.jp/api"
        self.rate_limiter = RateLimiter(requests_per_minute=30)
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Carbon-Emissions-Platform/1.0'
        })
    
    @handle_api_error(max_retries=3)
    def get_global_warming_potentials(self, assessment_report: str = "AR6") -> List[Dict]:
        """Fetch Global Warming Potentials from IPCC"""
        self.rate_limiter.wait_if_needed()
        
        # Return mock data for demo
        return self._get_mock_ipcc_data(assessment_report)
    
    def _get_mock_ipcc_data(self, assessment_report: str) -> List[Dict]:
        """Return mock IPCC data for testing"""
        return [{
            'name': 'Methane (CH4) GWP',
            'scope': 'Global Warming Potential',
            'category': 'GWP',
            'factor_value': 28.0,
            'unit': 'kg CO2e/kg',
            'source': 'IPCC',
            'region': 'Global',
            'year': 2021,
            'uncertainty': 15.0,
            'data_quality': 5.0,
            'metadata': {
                'assessment_report': assessment_report,
                'gas_formula': 'CH4',
                'lifetime_years': 12,
                'data_source': f'IPCC {assessment_report}'
            }
        }, {
            'name': 'Nitrous Oxide (N2O) GWP',
            'scope': 'Global Warming Potential',
            'category': 'GWP',
            'factor_value': 265.0,
            'unit': 'kg CO2e/kg',
            'source': 'IPCC',
            'region': 'Global',
            'year': 2021,
            'uncertainty': 20.0,
            'data_quality': 5.0,
            'metadata': {
                'assessment_report': assessment_report,
                'gas_formula': 'N2O',
                'lifetime_years': 109,
                'data_source': f'IPCC {assessment_report}'
            }
        }]
