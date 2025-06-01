import pytest
from unittest.mock import Mock, patch
from app.pipeline.api_clients import EPAClient, DEFRAClient, IPCCClient

class TestAPIIntegration:
    
    def test_epa_client_mock_data(self):
        """Test EPA client with mock data"""
        client = EPAClient()  # No API key, will use mock data
        factors = client.get_emission_factors(2023)
        
        assert len(factors) == 2
        assert factors[0]['source'] == 'EPA'
        assert factors[0]['region'] == 'US'
        assert factors[1]['scope'] == 'Scope 1'
    
    def test_defra_client_mock_data(self):
        """Test DEFRA client with mock data"""
        client = DEFRAClient()  # No API key, will use mock data
        factors = client.get_uk_emission_factors(2023)
        
        assert len(factors) == 2
        assert factors[0]['source'] == 'DEFRA'
        assert factors[0]['region'] == 'UK'
        assert factors[1]['scope'] == 'Scope 1'
    
    def test_ipcc_client_mock_data(self):
        """Test IPCC client with mock data"""
        client = IPCCClient()
        factors = client.get_global_warming_potentials('AR6')
        
        assert len(factors) == 2
        assert factors[0]['source'] == 'IPCC'
        assert 'GWP' in factors[0]['name']
        assert factors[0]['data_quality'] == 5.0
