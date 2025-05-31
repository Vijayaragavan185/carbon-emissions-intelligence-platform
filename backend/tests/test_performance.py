import pytest
import time
from app.core.calculation_engine import GHGCalculationEngine
from app.db.models.emissions import EmissionFactor, ScopeEnum
from sqlalchemy.orm import Session

class TestPerformance:
    
    def test_bulk_calculations(self, db: Session):
        """Test performance of bulk emission calculations"""
        # Create test emission factors
        factors = []
        for i in range(10):
            factor = EmissionFactor(
                name=f"Factor {i}",
                scope=ScopeEnum.SCOPE_1,
                category="Test",
                factor_value=0.1 + i * 0.01,
                unit="kg CO2e/unit",
                source="Test",
                year=2023
            )
            factors.append(factor)
        
        db.add_all(factors)
        db.commit()
        
        engine = GHGCalculationEngine(db)
        
        # Measure time for 1000 calculations
        start_time = time.time()
        
        for i in range(1000):
            result = engine.calculate_emission(100.0, 0.5)
            assert result['emission'] == 50.0
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        # Should complete 1000 calculations in under 1 second
        assert calculation_time < 1.0
        
        print(f"1000 calculations completed in {calculation_time:.4f} seconds")
