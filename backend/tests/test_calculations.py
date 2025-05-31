import pytest
from datetime import datetime
from app.core.calculation_engine import GHGCalculationEngine
from app.db.models.emissions import EmissionFactor, ScopeEnum
from sqlalchemy.orm import Session

class TestCalculations:
    
    def test_scope1_emissions(self, db: Session):
        """Test Scope 1 emissions calculation"""
        # Create test emission factor
        factor = EmissionFactor(
            name="Natural Gas",
            scope=ScopeEnum.SCOPE_1,
            category="Stationary Combustion",
            factor_value=0.0539,  # kg CO2e/kWh
            unit="kg CO2e/kWh",
            source="EPA",
            year=2023,
            is_active=True
        )
        db.add(factor)
        db.commit()

        engine = GHGCalculationEngine(db)

        fuel_data = [{
            'fuel_type': 'Stationary Combustion',
            'amount': 1000.0,
            'unit': 'kWh'
        }]

        result = engine.calculate_scope1_emissions(fuel_data)

        # Use pytest.approx() for floating point comparisons
        assert result['total_emissions'] == pytest.approx(53.9)
        assert len(result['calculations']) == 1
        assert result['calculations'][0]['emission'] == pytest.approx(53.9)
    
    def test_emission_factors(self, db: Session):
        """Test emission factor validation and retrieval"""
        factor = EmissionFactor(
            name="Electricity Grid",
            scope=ScopeEnum.SCOPE_2,
            category="Electricity",
            factor_value=0.4,
            unit="kg CO2e/kWh",
            source="IEA",
            region="US",
            year=2023,
            uncertainty=10.0,
            is_active=True
        )
        db.add(factor)
        db.commit()

        engine = GHGCalculationEngine(db)
        result = engine.calculate_scope2_emissions(1000.0, "US")

        # Use pytest.approx() for floating point comparisons
        assert result['emission'] == pytest.approx(400.0)
        assert 'uncertainty_range' in result
        assert result['uncertainty_range'][0] == pytest.approx(360.0)
        assert result['uncertainty_range'][1] == pytest.approx(440.0)
