from sqlalchemy.orm import Session
from app.db.models.emissions import Company, EmissionFactor, EmissionRecord, ScopeEnum
from app.db.session import SessionLocal
from datetime import datetime

def load_sample_data():
    """Load sample data for testing and demonstration"""
    db = SessionLocal()
    
    try:
        # Sample companies
        companies = [
            Company(
                name="EcoTech Industries",
                registration_number="12345678",
                industry_sector="Technology",
                country="US",
                reporting_year=2023
            ),
            Company(
                name="Green Manufacturing Ltd",
                registration_number="87654321",
                industry_sector="Manufacturing",
                country="UK",
                reporting_year=2023
            )
        ]
        
        # Sample emission factors
        emission_factors = [
            EmissionFactor(
                name="Natural Gas - Stationary Combustion",
                scope=ScopeEnum.SCOPE_1,
                category="Stationary Combustion",
                factor_value=0.0539,
                unit="kg CO2e/kWh",
                source="EPA eGRID 2021",
                region="US",
                year=2023
            ),
            EmissionFactor(
                name="Electricity - US Grid Average",
                scope=ScopeEnum.SCOPE_2,
                category="Electricity",
                factor_value=0.4091,
                unit="kg CO2e/kWh",
                source="EPA eGRID 2021",
                region="US",
                year=2023,
                uncertainty=15.0
            )
        ]
        
        db.add_all(companies + emission_factors)
        db.commit()
        
        print("Sample data loaded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error loading sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    load_sample_data()
