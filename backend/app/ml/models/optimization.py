import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy.optimize import minimize, differential_evolution
from scipy.optimize import linprog
import logging

logger = logging.getLogger(__name__)

class CarbonReductionOptimizer:
    """Optimize carbon reduction strategies"""
    
    def __init__(self):
        self.optimization_results = {}
        self.constraints = []
        self.objectives = []
    
    def define_reduction_problem(
        self,
        initiatives: List[Dict],
        budget_constraint: float,
        target_reduction: float
    ) -> Dict:
        """
        Define carbon reduction optimization problem
        
        initiatives: List of reduction initiatives with cost and impact
        budget_constraint: Maximum budget available
        target_reduction: Target carbon reduction (tonnes CO2e)
        """
        try:
            self.initiatives = initiatives
            self.budget_constraint = budget_constraint
            self.target_reduction = target_reduction
            self.num_initiatives = len(initiatives)
            
            # Extract costs and impacts
            self.costs = np.array([init['cost'] for init in initiatives])
            self.impacts = np.array([init['co2_reduction'] for init in initiatives])
            self.names = [init['name'] for init in initiatives]
            
            logger.info(f"Optimization problem defined with {self.num_initiatives} initiatives")
            logger.info(f"Budget constraint: ${budget_constraint:,.2f}")
            logger.info(f"Target reduction: {target_reduction:,.2f} tonnes CO2e")
            
            return {
                'num_initiatives': self.num_initiatives,
                'total_potential_reduction': float(np.sum(self.impacts)),
                'total_cost_if_all': float(np.sum(self.costs)),
                'cost_effectiveness_ratios': (self.impacts / self.costs).tolist()
            }
            
        except Exception as e:
            logger.error(f"Error defining optimization problem: {e}")
            raise
    
    def cost_effectiveness_optimization(self) -> Dict:
        """Optimize based on cost-effectiveness ratios"""
        try:
            # Calculate cost-effectiveness ratios (CO2 reduction per dollar)
            ratios = self.impacts / self.costs
            
            # Sort by cost-effectiveness (descending)
            sorted_indices = np.argsort(ratios)[::-1]
            
            selected_initiatives = []
            total_cost = 0
            total_reduction = 0
            
            for idx in sorted_indices:
                if total_cost + self.costs[idx] <= self.budget_constraint:
                    selected_initiatives.append({
                        'index': int(idx),
                        'name': self.names[idx],
                        'cost': float(self.costs[idx]),
                        'reduction': float(self.impacts[idx]),
                        'ratio': float(ratios[idx])
                    })
                    total_cost += self.costs[idx]
                    total_reduction += self.impacts[idx]
            
            results = {
                'method': 'cost_effectiveness',
                'selected_initiatives': selected_initiatives,
                'total_cost': float(total_cost),
                'total_reduction': float(total_reduction),
                'budget_utilization': float(total_cost / self.budget_constraint),
                'target_achievement': float(total_reduction / self.target_reduction),
                'average_cost_per_tonne': float(total_cost / total_reduction) if total_reduction > 0 else 0
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in cost-effectiveness optimization: {e}")
            raise
    
    def linear_programming_optimization(self) -> Dict:
        """Use linear programming for optimization"""
        try:
            # Objective: maximize carbon reduction
            # Constraints: budget limit, binary selection
            
            # For LP, we'll use continuous variables [0,1] representing implementation level
            c = -self.impacts  # Negative because linprog minimizes
            
            # Budget constraint: sum(costs * x) <= budget
            A_ub = [self.costs]
            b_ub = [self.budget_constraint]
            
            # Bounds: 0 <= x <= 1 for each initiative
            bounds = [(0, 1) for _ in range(self.num_initiatives)]
            
            # Solve
            result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
            
            if result.success:
                # Extract solution
                selection = result.x
                total_cost = float(np.sum(selection * self.costs))
                total_reduction = float(np.sum(selection * self.impacts))
                
                selected_initiatives = []
                for i, level in enumerate(selection):
                    if level > 0.01:  # Include if implementation level > 1%
                        selected_initiatives.append({
                            'index': int(i),
                            'name': self.names[i],
                            'implementation_level': float(level),
                            'cost': float(level * self.costs[i]),
                            'reduction': float(level * self.impacts[i])
                        })
                
                results = {
                    'method': 'linear_programming',
                    'success': True,
                    'selected_initiatives': selected_initiatives,
                    'total_cost': total_cost,
                    'total_reduction': total_reduction,
                    'budget_utilization': total_cost / self.budget_constraint,
                    'target_achievement': total_reduction / self.target_reduction,
                    'optimization_value': float(-result.fun)
                }
            else:
                results = {
                    'method': 'linear_programming',
                    'success': False,
                    'message': 'Optimization failed',
                    'error': result.message
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in linear programming optimization: {e}")
            raise
    
    def genetic_algorithm_optimization(self) -> Dict:
        """Use genetic algorithm for optimization"""
        try:
            def objective_function(x):
                """Objective: maximize reduction while staying within budget"""
                # x is binary array indicating selected initiatives
                x_binary = (x > 0.5).astype(int)
                
                total_cost = np.sum(x_binary * self.costs)
                total_reduction = np.sum(x_binary * self.impacts)
                
                # Penalty for exceeding budget
                if total_cost > self.budget_constraint:
                    penalty = 1000 * (total_cost - self.budget_constraint)
                    return -total_reduction + penalty
                
                return -total_reduction  # Negative because we minimize
            
            # Bounds for binary variables
            bounds = [(0, 1) for _ in range(self.num_initiatives)]
            
            # Run genetic algorithm
            result = differential_evolution(
                objective_function,
                bounds,
                seed=42,
                maxiter=100,
                popsize=15
            )
            
            if result.success:
                # Convert to binary selection
                selection = (result.x > 0.5).astype(int)
                total_cost = float(np.sum(selection * self.costs))
                total_reduction = float(np.sum(selection * self.impacts))
                
                selected_initiatives = []
                for i, selected in enumerate(selection):
                    if selected:
                        selected_initiatives.append({
                            'index': int(i),
                            'name': self.names[i],
                            'cost': float(self.costs[i]),
                            'reduction': float(self.impacts[i])
                        })
                
                results = {
                    'method': 'genetic_algorithm',
                    'success': True,
                    'selected_initiatives': selected_initiatives,
                    'total_cost': total_cost,
                    'total_reduction': total_reduction,
                    'budget_utilization': total_cost / self.budget_constraint,
                    'target_achievement': total_reduction / self.target_reduction,
                    'optimization_value': float(-result.fun)
                }
            else:
                results = {
                    'method': 'genetic_algorithm',
                    'success': False,
                    'message': 'Optimization failed'
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in genetic algorithm optimization: {e}")
            raise
    
    def multi_objective_optimization(self) -> Dict:
        """Optimize for multiple objectives (cost, reduction, risk)"""
        try:
            # Add risk scores if available
            risks = np.array([init.get('risk_score', 0.5) for init in self.initiatives])
            
            def multi_objective(x):
                """Multi-objective function balancing cost, reduction, and risk"""
                x_binary = (x > 0.5).astype(int)
                
                total_cost = np.sum(x_binary * self.costs)
                total_reduction = np.sum(x_binary * self.impacts)
                total_risk = np.sum(x_binary * risks)
                
                # Penalty for exceeding budget
                if total_cost > self.budget_constraint:
                    return 1e6
                
                # Weighted objective: maximize reduction, minimize cost and risk
                reduction_weight = 0.6
                cost_weight = 0.3
                risk_weight = 0.1
                
                # Normalize values
                norm_reduction = total_reduction / np.sum(self.impacts)
                norm_cost = total_cost / self.budget_constraint
                norm_risk = total_risk / len(self.initiatives)
                
                # Minimize (negative reduction + cost + risk)
                objective = -(reduction_weight * norm_reduction) + \
                           (cost_weight * norm_cost) + \
                           (risk_weight * norm_risk)
                
                return objective
            
            bounds = [(0, 1) for _ in range(self.num_initiatives)]
            
            result = differential_evolution(
                multi_objective,
                bounds,
                seed=42,
                maxiter=150
            )
            
            if result.success:
                selection = (result.x > 0.5).astype(int)
                total_cost = float(np.sum(selection * self.costs))
                total_reduction = float(np.sum(selection * self.impacts))
                total_risk = float(np.sum(selection * risks))
                
                selected_initiatives = []
                for i, selected in enumerate(selection):
                    if selected:
                        selected_initiatives.append({
                            'index': int(i),
                            'name': self.names[i],
                            'cost': float(self.costs[i]),
                            'reduction': float(self.impacts[i]),
                            'risk_score': float(risks[i])
                        })
                
                results = {
                    'method': 'multi_objective',
                    'success': True,
                    'selected_initiatives': selected_initiatives,
                    'total_cost': total_cost,
                    'total_reduction': total_reduction,
                    'total_risk': total_risk,
                    'budget_utilization': total_cost / self.budget_constraint,
                    'target_achievement': total_reduction / self.target_reduction,
                    'risk_level': 'low' if total_risk < 0.3 else 'medium' if total_risk < 0.7 else 'high'
                }
            else:
                results = {
                    'method': 'multi_objective',
                    'success': False,
                    'message': 'Optimization failed'
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in multi-objective optimization: {e}")
            raise
    
    def run_all_optimizations(self) -> Dict:
        """Run all optimization methods and compare results"""
        try:
            methods = [
                ('cost_effectiveness', self.cost_effectiveness_optimization),
                ('linear_programming', self.linear_programming_optimization),
                ('genetic_algorithm', self.genetic_algorithm_optimization),
                ('multi_objective', self.multi_objective_optimization)
            ]
            
            results = {}
            best_method = None
            best_score = -float('inf')
            
            for method_name, method_func in methods:
                logger.info(f"Running {method_name} optimization...")
                
                try:
                    result = method_func()
                    results[method_name] = result
                    
                    # Compare based on target achievement and budget utilization
                    if result.get('success', True):
                        score = (result.get('target_achievement', 0) * 0.7 + 
                                (1 - result.get('budget_utilization', 1)) * 0.3)
                        
                        if score > best_score:
                            best_score = score
                            best_method = method_name
                            
                except Exception as e:
                    logger.error(f"Error in {method_name}: {e}")
                    results[method_name] = {'success': False, 'error': str(e)}
            
            # Summary
            summary = {
                'optimization_results': results,
                'best_method': best_method,
                'best_score': best_score,
                'comparison': self._compare_methods(results),
                'recommendations': self._generate_recommendations(results)
            }
            
            self.optimization_results = summary
            return summary
            
        except Exception as e:
            logger.error(f"Error running optimizations: {e}")
            raise
    
    def _compare_methods(self, results: Dict) -> Dict:
        """Compare optimization methods"""
        comparison = {}
        
        for method, result in results.items():
            if result.get('success', True):
                comparison[method] = {
                    'total_reduction': result.get('total_reduction', 0),
                    'total_cost': result.get('total_cost', 0),
                    'budget_utilization': result.get('budget_utilization', 0),
                    'target_achievement': result.get('target_achievement', 0),
                    'num_initiatives': len(result.get('selected_initiatives', []))
                }
        
        return comparison
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Find method with highest reduction
        max_reduction = 0
        best_reduction_method = None
        
        for method, result in results.items():
            if result.get('success', True):
                reduction = result.get('total_reduction', 0)
                if reduction > max_reduction:
                    max_reduction = reduction
                    best_reduction_method = method
        
        if best_reduction_method:
            recommendations.append(
                f"For maximum carbon reduction, use {best_reduction_method} method "
                f"achieving {max_reduction:.1f} tonnes CO2e reduction"
            )
        
        # Check budget efficiency
        for method, result in results.items():
            if result.get('success', True):
                utilization = result.get('budget_utilization', 0)
                if utilization < 0.8:
                    recommendations.append(
                        f"{method} method uses only {utilization*100:.1f}% of budget - "
                        f"consider additional initiatives"
                    )
        
        return recommendations
