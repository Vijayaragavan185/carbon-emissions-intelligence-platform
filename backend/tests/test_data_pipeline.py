import pytest
from app.pipeline.ingestion import DataIngestionPipeline
from sqlalchemy.orm import Session

class TestDataPipeline:
    
    def test_epa_integration(self, db: Session):
        """Test EPA data integration"""
        pipeline = DataIngestionPipeline(db)
        
        results = pipeline._sync_epa_data()
        
        assert results['processed'] >= 0
        assert 'inserted' in results
        assert 'updated' in results
        assert 'errors' in results
    
    def test_full_sync(self, db: Session):
        """Test full synchronization"""
        pipeline = DataIngestionPipeline(db)
        
        results = pipeline.run_full_sync()
        
        assert 'total_processed' in results
        assert 'sources' in results
        assert 'EPA' in results['sources']
        assert 'DEFRA' in results['sources']
        assert 'IPCC' in results['sources']
    
    def test_data_transformation(self, db: Session):
        """Test data transformation"""
        pipeline = DataIngestionPipeline(db)
        
        raw_data = [{
            'name': 'Test Factor',
            'scope': 'scope 1',
            'category': 'Test Category',
            'factor_value': '0.5',
            'unit': 'kg co2e/kwh',
            'source': 'Test',
            'year': 2023
        }]
        
        transformed = pipeline.transformer.transform(raw_data)
        
        assert len(transformed) == 1
        assert transformed[0]['scope'] == 'SCOPE_1'
        assert transformed[0]['factor_value'] == 0.5
        assert transformed[0]['unit'] == 'kg CO2e/kWh'
