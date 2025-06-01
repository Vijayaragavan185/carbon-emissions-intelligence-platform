from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmissionFactorTransformer:
    """Transform emission factor data from various sources"""
    
    def transform(self, raw_data: List[Dict]) -> List[Dict]:
        """Transform raw emission factor data"""
        transformed_data = []
        
        for item in raw_data:
            try:
                transformed_item = self._transform_item(item)
                if self.validate(transformed_item):
                    transformed_data.append(transformed_item)
                else:
                    logger.warning(f"Validation failed for item: {item.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error transforming item {item.get('name', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_data)} out of {len(raw_data)} items")
        return transformed_data
    
    def _transform_item(self, item: Dict) -> Dict:
        """Transform a single emission factor item"""
        return {
            'name': str(item.get('name', '')).strip(),
            'scope': self._standardize_scope(item.get('scope', '')),
            'category': str(item.get('category', '')).strip(),
            'subcategory': str(item.get('subcategory', '')).strip() if item.get('subcategory') else None,
            'factor_value': self._clean_numeric_value(item.get('factor_value', 0)),
            'unit': self._standardize_unit(str(item.get('unit', ''))),
            'source': str(item.get('source', '')).strip(),
            'region': str(item.get('region', 'Global')).strip(),
            'year': int(item.get('year', datetime.now().year)),
            'uncertainty': self._clean_numeric_value(item.get('uncertainty')) if item.get('uncertainty') else None,
            'data_quality': min(5.0, max(1.0, self._clean_numeric_value(item.get('data_quality', 3.0)))),
            'last_updated': datetime.utcnow(),
            'is_active': True,
            'metadata': item.get('metadata', {})
        }
    
    def _standardize_scope(self, scope: str) -> str:
        """Standardize scope naming"""
        scope_lower = str(scope).lower()
        
        if 'scope 1' in scope_lower or 'scope1' in scope_lower:
            return 'SCOPE_1'
        elif 'scope 2' in scope_lower or 'scope2' in scope_lower:
            return 'SCOPE_2'
        elif 'scope 3' in scope_lower or 'scope3' in scope_lower:
            return 'SCOPE_3'
        else:
            # Try to infer from content
            if 'electricity' in scope_lower or 'grid' in scope_lower:
                return 'SCOPE_2'
            elif any(word in scope_lower for word in ['transport', 'delivery', 'waste', 'purchased']):
                return 'SCOPE_3'
            else:
                return 'SCOPE_1'
    
    def _standardize_unit(self, unit: str) -> str:
        """Standardize unit naming"""
        unit_mapping = {
            'kg co2e/mwh': 'kg CO2e/MWh',
            'kg co2e/kwh': 'kg CO2e/kWh',
            'kg co2e/unit': 'kg CO2e/unit',
            'kg co2e/liter': 'kg CO2e/L',
            'kg co2e/gallon': 'kg CO2e/gal',
            'kg co2e/kg': 'kg CO2e/kg',
            'kg co2e/tonne': 'kg CO2e/t'
        }
        
        return unit_mapping.get(unit.lower().strip(), unit)
    
    def _clean_numeric_value(self, value) -> float:
        """Clean and convert numeric values"""
        if value is None:
            return 0.0
        
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert value to float: {value}")
            return 0.0
    
    def validate(self, data: Dict) -> bool:
        """Validate transformed emission factor data"""
        required_fields = ['name', 'scope', 'category', 'factor_value', 'unit', 'source']
        
        # Check required fields
        for field in required_fields:
            if not data.get(field):
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate numeric fields
        if data['factor_value'] <= 0:
            logger.warning(f"Invalid factor_value: {data['factor_value']}")
            return False
        
        # Validate scope
        valid_scopes = ['SCOPE_1', 'SCOPE_2', 'SCOPE_3']
        if data['scope'] not in valid_scopes:
            logger.warning(f"Invalid scope: {data['scope']}")
            return False
        
        # Validate year
        current_year = datetime.now().year
        if data['year'] < 1990 or data['year'] > current_year + 1:
            logger.warning(f"Invalid year: {data['year']}")
            return False
        
        return True
