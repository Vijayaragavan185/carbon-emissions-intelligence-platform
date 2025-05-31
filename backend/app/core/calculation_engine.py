from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models.emissions import EmissionRecord, EmissionFactor, ScopeEnum
import math

class GHGCalculationEngine:
    """GHG Protocol compliant calculation engine for carbon emissions"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def calculate_emission(
        self, 
        activity_amount: float, 
        emission_factor: float,
        uncertainty: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate emissions using GHG Protocol methodology
        Returns: {'emission': value, 'uncertainty_range': (min, max)}
        """
        if activity_amount < 0:
            raise ValueError("Activity amount must be non-negative")
        if emission_factor <= 0:
            raise ValueError("Emission factor must be positive")
            
        emission = activity_amount * emission_factor
        
        result = {'emission': emission}
        
        if uncertainty:
            uncertainty_value = emission * (uncertainty / 100)
            result['uncertainty_range'] = (
                emission - uncertainty_value,
                emission + uncertainty_value
            )
            
        return result
    
    def calculate_scope1_emissions(
        self, 
        fuel_data: List[Dict]
    ) -> Dict[str, float]:
        """
        Calculate Scope 1 emissions from fuel combustion
        fuel_data: [{'fuel_type': str, 'amount': float, 'unit': str}]
        """
        total_emissions = 0.0
        calculations = []
        
        for fuel in fuel_data:
            factor = self._get_emission_factor(
                ScopeEnum.SCOPE_1, 
                fuel['fuel_type']
            )
            
            if factor:
                calc = self.calculate_emission(
                    fuel['amount'], 
                    factor.factor_value,
                    factor.uncertainty
                )
                total_emissions += calc['emission']
                calculations.append({
                    'fuel_type': fuel['fuel_type'],
                    'amount': fuel['amount'],
                    'factor': factor.factor_value,
                    'emission': calc['emission']
                })
        
        return {
            'total_emissions': total_emissions,
            'calculations': calculations
        }
    
    def calculate_scope2_emissions(
        self, 
        electricity_kwh: float, 
        location: str = "US"
    ) -> Dict[str, float]:
        """Calculate Scope 2 emissions from electricity consumption"""
        factor = self._get_electricity_factor(location)
        
        if not factor:
            raise ValueError(f"No electricity factor found for location: {location}")
            
        return self.calculate_emission(
            electricity_kwh, 
            factor.factor_value,
            factor.uncertainty
        )
    
    def validate_data_quality(
        self, 
        emission_record: EmissionRecord
    ) -> Tuple[bool, List[str]]:
        """Validate emission data quality according to GHG Protocol"""
        issues = []
        
        # Check data completeness
        if not emission_record.activity_amount:
            issues.append("Missing activity amount")
        
        if not emission_record.emission_factor_id:
            issues.append("Missing emission factor")
            
        # Check data reasonableness
        if emission_record.activity_amount > 10**6:  # Very large values
            issues.append("Activity amount seems unusually large")
            
        # Check temporal consistency
        if emission_record.reporting_period_start >= emission_record.reporting_period_end:
            issues.append("Invalid reporting period")
            
        return len(issues) == 0, issues
    
    def _get_emission_factor(
        self, 
        scope: ScopeEnum, 
        activity_type: str
    ) -> Optional[EmissionFactor]:
        """Get emission factor for specific scope and activity"""
        return self.db.query(EmissionFactor).filter(
            EmissionFactor.scope == scope,
            EmissionFactor.category == activity_type,
            EmissionFactor.is_active == True
        ).first()
    
    def _get_electricity_factor(self, location: str) -> Optional[EmissionFactor]:
        """Get electricity emission factor for location"""
        return self.db.query(EmissionFactor).filter(
            EmissionFactor.scope == ScopeEnum.SCOPE_2,
            EmissionFactor.region == location,
            EmissionFactor.category == "Electricity",
            EmissionFactor.is_active == True
        ).first()
