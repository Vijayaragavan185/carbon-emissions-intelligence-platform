import pytest
from app.db.models.emissions import Company, EmissionRecord, EmissionFactor, ScopeEnum
from sqlalchemy.orm import Session
from datetime import datetime

class TestModels:
    
    def test_data_relationships(self, db: Session):
        """Test database model relationships"""
        # Create parent company
        parent = Company(
            name="Parent Corp",
            industry_sector="Manufacturing",
            country="US",
            reporting_year=2023
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)  # Refresh to get the ID
        
        # Create child company
        child = Company(
            name="Subsidiary Corp",
            industry_sector="Manufacturing",
            country="US",
            parent_id=parent.id,
            reporting_year=2023
        )
        db.add(child)
        db.commit()
        db.refresh(child)  # Refresh to load relationships
        
        # Create emission factor
        factor = EmissionFactor(
            name="Natural Gas",
            scope=ScopeEnum.SCOPE_1,
            category="Fuel",
            factor_value=0.2,
            unit="kg CO2e/kWh",
            source="EPA",
            year=2023
        )
        db.add(factor)
        db.commit()
        
        # Create emission record
        record = EmissionRecord(
            company_id=child.id,
            scope=ScopeEnum.SCOPE_1,
            activity_type="Fuel",
            activity_amount=100.0,
            activity_unit="kWh",
            emission_factor_id=factor.id,
            calculated_emission=20.0,
            reporting_period_start=datetime(2023, 1, 1),
            reporting_period_end=datetime(2023, 12, 31)
        )
        db.add(record)
        db.commit()
        db.refresh(record)  # Refresh to load relationships
        
        # Test relationships
        assert child.parent == parent
        assert child in parent.children
        assert record.company == child
        assert record.emission_factor == factor
        assert child.total_emissions == pytest.approx(20.0)
