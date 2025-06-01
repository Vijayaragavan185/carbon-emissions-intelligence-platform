import pytest
from app.pipeline.quality import DataQualityAssessor

class TestDataQuality:
    
    def test_high_quality_assessment(self):
        """Test high quality data assessment"""
        assessor = DataQualityAssessor()
        
        high_quality_factor = {
            'name': 'Natural Gas',
            'scope': 'SCOPE_1',
            'category': 'Stationary Combustion',
            'factor_value': 0.0539,
            'unit': 'kg CO2e/kWh',
            'source': 'EPA',
            'region': 'US',
            'year': 2023,
            'uncertainty': 5.0,
            'metadata': {'methodology': 'IPCC Guidelines'}
        }
        
        score, issues = assessor._calculate_quality_score(high_quality_factor)
        
        assert score >= 4.0
        assert len(issues) == 0
    
    def test_low_quality_detection(self):
        """Test detection of low quality data"""
        assessor = DataQualityAssessor()
        
        low_quality_factor = {
            'name': '',
            'scope': '',
            'category': '',
            'factor_value': 0,
            'unit': '',
            'source': '',
            'year': 1980
        }
        
        score, issues = assessor._calculate_quality_score(low_quality_factor)
        
        assert score < 3.0
        assert len(issues) > 0
    
    def test_quality_assessment_batch(self):
        """Test batch quality assessment"""
        assessor = DataQualityAssessor()
        
        factors = [{
            'name': 'Good Factor',
            'scope': 'SCOPE_1',
            'category': 'Test',
            'factor_value': 0.5,
            'unit': 'kg CO2e/unit',
            'source': 'Test',
            'year': 2023
        }, {
            'name': 'Poor Factor',
            'scope': '',
            'category': '',
            'factor_value': 0,
            'unit': '',
            'source': '',
            'year': 1990
        }]
        
        assessed = assessor.assess_data_quality(factors)
        
        assert len(assessed) == 2
        assert assessed[0]['data_quality'] > assessed[1]['data_quality']
