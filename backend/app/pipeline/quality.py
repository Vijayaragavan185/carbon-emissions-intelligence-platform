from typing import Dict, List, Tuple
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from app.db.models.emissions import EmissionFactor

logger = logging.getLogger(__name__)

class DataQualityAssessor:
    """Assess and score data quality for emission factors"""
    
    def __init__(self, db: Session = None):
        self.db = db
    
    def assess_data_quality(self, emission_factors: List[Dict]) -> List[Dict]:
        """Assess data quality for a list of emission factors"""
        assessed_factors = []
        
        for factor in emission_factors:
            quality_score, quality_issues = self._calculate_quality_score(factor)
            factor['data_quality'] = quality_score
            factor['quality_issues'] = quality_issues
            assessed_factors.append(factor)
            
            logger.info(f"Quality assessment: {factor.get('name')} - Score: {quality_score}/5.0")
            if quality_issues:
                logger.warning(f"Quality issues: {', '.join(quality_issues)}")
        
        return assessed_factors
    
    def _calculate_quality_score(self, factor: Dict) -> Tuple[float, List[str]]:
        """Calculate comprehensive data quality score (1-5 scale)"""
        issues = []
        
        # Completeness check (40% weight)
        completeness_score, completeness_issues = self._assess_completeness(factor)
        issues.extend(completeness_issues)
        
        # Accuracy check (30% weight)
        accuracy_score, accuracy_issues = self._assess_accuracy(factor)
        issues.extend(accuracy_issues)
        
        # Timeliness check (30% weight)
        timeliness_score, timeliness_issues = self._assess_timeliness(factor)
        issues.extend(timeliness_issues)
        
        # Calculate weighted average
        final_score = (completeness_score * 0.4 + accuracy_score * 0.3 + timeliness_score * 0.3)
        
        return round(max(1.0, min(5.0, final_score)), 2), issues
    
    def _assess_completeness(self, factor: Dict) -> Tuple[float, List[str]]:
        """Assess data completeness"""
        score = 5.0
        issues = []
        
        required_fields = ['name', 'scope', 'category', 'factor_value', 'unit', 'source']
        optional_fields = ['subcategory', 'region', 'uncertainty', 'metadata']
        
        # Check required fields
        missing_required = [field for field in required_fields if not factor.get(field)]
        if missing_required:
            score -= len(missing_required) * 0.8  # More severe penalty
            issues.append(f"Missing required fields: {', '.join(missing_required)}")
        
        # Check optional fields
        missing_optional = [field for field in optional_fields if not factor.get(field)]
        if missing_optional:
            score -= len(missing_optional) * 0.1  # Minor penalty
        
        return max(1.0, score), issues
    
    def _assess_accuracy(self, factor: Dict) -> Tuple[float, List[str]]:
        """Assess data accuracy"""
        score = 5.0
        issues = []
        
        # Check for reasonable factor values
        factor_value = factor.get('factor_value', 0)
        if factor_value <= 0:
            score -= 3.0  # Severe penalty for invalid values
            issues.append("Factor value is zero or negative")
        elif factor_value > 10000:  # Unreasonably high
            score -= 1.0
            issues.append("Factor value seems unreasonably high")
        
        # Check uncertainty if provided
        uncertainty = factor.get('uncertainty')
        if uncertainty and uncertainty > 100:
            score -= 0.5
            issues.append("Uncertainty value seems unreasonably high")
        
        # Check unit consistency
        unit = factor.get('unit', '')
        if not any(expected in unit.lower() for expected in ['co2', 'co2e', 'carbon']):
            score -= 1.0  # Penalty for wrong unit
            issues.append("Unit doesn't appear to be CO2 equivalent")
        
        return max(1.0, score), issues
    
    def _assess_timeliness(self, factor: Dict) -> Tuple[float, List[str]]:
        """Assess data timeliness"""
        score = 5.0
        issues = []
        
        current_year = datetime.now().year
        data_year = factor.get('year', current_year)
        
        age = current_year - data_year
        
        if age > 10:  # Very old data
            score -= 3.0
            issues.append(f"Data is {age} years old")
        elif age > 5:
            score -= 2.0
            issues.append(f"Data is {age} years old")
        elif age > 3:
            score -= 1.0
            issues.append(f"Data is {age} years old")
        elif age > 1:
            score -= 0.5
        
        return max(1.0, score), issues
