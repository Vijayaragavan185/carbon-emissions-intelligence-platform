"""Database models package"""

# Import all models from the models.py file
try:
    from ..models import (
        Company,
        EmissionRecord, 
        EmissionFactor,
        AuditTrail,
        DataValidationLog,
        CalculationMethod,
        Emission,
        ScopeEnum
    )
    
    __all__ = [
        "Company",
        "EmissionRecord", 
        "EmissionFactor",
        "AuditTrail",
        "DataValidationLog", 
        "CalculationMethod",
        "Emission",
        "ScopeEnum"
    ]
    
except ImportError as e:
    print(f"Warning: Could not import models: {e}")
    # Provide empty exports to prevent import errors
    __all__ = []
