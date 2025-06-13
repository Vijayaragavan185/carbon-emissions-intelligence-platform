#!/usr/bin/env python3
"""Fix the remaining 2 ML model issues"""

import os

def fix_scenario_modeling():
    """Add missing methods to scenario_modeling.py"""
    file_path = "app/ml/models/scenario_modeling.py"
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Add the missing methods before the last method
        missing_methods = '''
    def _analyze_target_feasibility(self, scenario: Dict) -> Dict:
        """Analyze feasibility of achieving target reduction"""
        try:
            target_reduction = scenario.get('target_reduction', 0)
            target_year = scenario.get('target_year', 2030)
            recommended_interventions = scenario.get('recommended_interventions', [])
            
            # Calculate total potential reduction from recommended interventions
            total_potential_reduction = sum(
                intervention.get('annual_reduction', 0) 
                for intervention in recommended_interventions
            )
            
            # Calculate total cost
            total_cost = sum(
                intervention.get('cost', 0) 
                for intervention in recommended_interventions
            )
            
            # Feasibility analysis
            feasibility_score = min(total_potential_reduction / target_reduction, 1.0) if target_reduction > 0 else 0
            
            # Risk assessment
            implementation_complexity = np.mean([
                intervention.get('implementation_duration', 1) 
                for intervention in recommended_interventions
            ]) if recommended_interventions else 0
            
            risk_level = 'low' if feasibility_score > 0.8 and implementation_complexity < 2 else \\
                        'medium' if feasibility_score > 0.5 else 'high'
            
            return {
                'feasibility_score': float(feasibility_score),
                'is_achievable': feasibility_score >= 0.8,
                'total_potential_reduction': float(total_potential_reduction),
                'reduction_gap': float(max(0, target_reduction - total_potential_reduction)),
                'total_cost': float(total_cost),
                'risk_level': risk_level,
                'implementation_complexity': float(implementation_complexity),
                'confidence': 'high' if feasibility_score > 0.9 else 'medium' if feasibility_score > 0.6 else 'low',
                'recommendations': self._generate_feasibility_recommendations(feasibility_score, target_reduction, total_potential_reduction)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing target feasibility: {e}")
            return {
                'feasibility_score': 0.0,
                'is_achievable': False,
                'error': str(e)
            }

    def _generate_feasibility_recommendations(self, feasibility_score: float, target_reduction: float, potential_reduction: float) -> List[str]:
        """Generate recommendations based on feasibility analysis"""
        recommendations = []
        
        if feasibility_score >= 0.9:
            recommendations.append("Target is highly achievable with current intervention portfolio")
        elif feasibility_score >= 0.7:
            recommendations.append("Target is achievable but may require optimization of implementation timeline")
        elif feasibility_score >= 0.5:
            recommendations.append("Target is challenging - consider additional interventions or extending timeline")
            if target_reduction - potential_reduction > 0.1:
                recommendations.append(f"Consider additional interventions to close {(target_reduction - potential_reduction)*100:.1f}% reduction gap")
        else:
            recommendations.append("Target may not be achievable with current approach - significant changes needed")
            recommendations.append("Consider revising target reduction percentage or extending timeline")
        
        return recommendations
'''
        
        # Insert before the last method
        if 'def _analyze_trade_offs' in content:
            content = content.replace(
                '    def _analyze_trade_offs',
                missing_methods + '\n    def _analyze_trade_offs'
            )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✅ Added missing feasibility analysis methods")

def fix_pandas_warning():
    """Fix pandas fillna warning"""
    file_path = "app/ml/models/forecasting.py"
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix fillna warning
        content = content.replace(
            "emission_data.fillna(method='ffill').fillna(method='bfill')",
            "emission_data.ffill().bfill()"
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✅ Fixed pandas fillna warning")

if __name__ == "__main__":
    print("🔧 Fixing remaining ML issues...")
    fix_scenario_modeling()
    fix_pandas_warning()
    print("✅ All fixes applied!")
