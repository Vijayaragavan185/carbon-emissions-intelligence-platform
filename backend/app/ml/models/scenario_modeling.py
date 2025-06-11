import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)

class CarbonScenarioModeler:
    """Model different carbon reduction scenarios and their impacts"""
    
    def __init__(self):
        self.baseline_scenario = None
        self.scenarios = {}
        self.comparison_results = {}
        
    def create_baseline_scenario(self, company_data: Dict) -> Dict:
        """Create baseline scenario (business as usual)"""
        try:
            baseline = {
                'name': 'Business as Usual',
                'type': 'baseline',
                'description': 'Current trajectory without additional interventions',
                'parameters': {
                    'current_emissions': company_data.get('annual_emissions', 0),
                    'historical_growth_rate': company_data.get('emission_growth_rate', 0.02),
                    'business_growth_rate': company_data.get('business_growth_rate', 0.05),
                    'efficiency_improvement': company_data.get('natural_efficiency', 0.01)
                },
                'timeline_years': company_data.get('scenario_timeline', 10),
                'interventions': [],
                'created_at': datetime.now().isoformat()
            }
            
            # Project baseline emissions
            baseline['projections'] = self._project_emissions(baseline)
            
            self.baseline_scenario = baseline
            return baseline
            
        except Exception as e:
            logger.error(f"Error creating baseline scenario: {e}")
            raise
    
    def create_intervention_scenario(
        self,
        name: str,
        interventions: List[Dict],
        description: str = ""
    ) -> Dict:
        """Create scenario with specific interventions"""
        try:
            if not self.baseline_scenario:
                raise ValueError("Baseline scenario must be created first")
            
            scenario = {
                'name': name,
                'type': 'intervention',
                'description': description,
                'parameters': deepcopy(self.baseline_scenario['parameters']),
                'timeline_years': self.baseline_scenario['timeline_years'],
                'interventions': interventions,
                'created_at': datetime.now().isoformat()
            }
            
            # Validate interventions
            validated_interventions = self._validate_interventions(interventions)
            scenario['interventions'] = validated_interventions
            
            # Project emissions with interventions
            scenario['projections'] = self._project_emissions_with_interventions(scenario)
            
            # Calculate impact metrics
            scenario['impact_metrics'] = self._calculate_scenario_impact(scenario)
            
            self.scenarios[name] = scenario
            return scenario
            
        except Exception as e:
            logger.error(f"Error creating intervention scenario: {e}")
            raise
    
    def create_target_scenario(
        self,
        target_reduction: float,
        target_year: int,
        optimization_strategy: str = 'cost_effective'
    ) -> Dict:
        """Create scenario to meet specific reduction target"""
        try:
            if not self.baseline_scenario:
                raise ValueError("Baseline scenario must be created first")
            
            current_year = datetime.now().year
            years_to_target = target_year - current_year
            
            if years_to_target <= 0:
                raise ValueError("Target year must be in the future")
            
            # Calculate required annual reduction rate
            current_emissions = self.baseline_scenario['parameters']['current_emissions']
            target_emissions = current_emissions * (1 - target_reduction)
            required_rate = target_reduction / years_to_target
            
            scenario = {
                'name': f'{target_reduction*100:.0f}% Reduction by {target_year}',
                'type': 'target',
                'description': f'Scenario to achieve {target_reduction*100:.0f}% emission reduction by {target_year}',
                'parameters': deepcopy(self.baseline_scenario['parameters']),
                'timeline_years': years_to_target,
                'target_reduction': target_reduction,
                'target_year': target_year,
                'target_emissions': target_emissions,
                'required_annual_rate': required_rate,
                'optimization_strategy': optimization_strategy,
                'created_at': datetime.now().isoformat()
            }
            
            # Generate intervention recommendations
            scenario['recommended_interventions'] = self._recommend_interventions_for_target(
                target_reduction, years_to_target, optimization_strategy
            )
            
            # Project emissions
            scenario['projections'] = self._project_target_scenario(scenario)
            
            # Calculate feasibility
            scenario['feasibility_analysis'] = self._analyze_target_feasibility(scenario)
            
            self.scenarios[scenario['name']] = scenario
            return scenario
            
        except Exception as e:
            logger.error(f"Error creating target scenario: {e}")
            raise
    
    def _project_emissions(self, scenario: Dict) -> Dict:
        """Project emissions for baseline scenario"""
        try:
            params = scenario['parameters']
            timeline_years = scenario['timeline_years']
            
            current_emissions = params['current_emissions']
            growth_rate = params.get('business_growth_rate', 0.05)
            efficiency_rate = params.get('efficiency_improvement', 0.01)
            
            # Net growth rate (business growth - efficiency improvements)
            net_growth_rate = growth_rate - efficiency_rate
            
            projections = {
                'years': list(range(datetime.now().year, datetime.now().year + timeline_years + 1)),
                'emissions': [],
                'cumulative_emissions': [],
                'emission_intensity': []
            }
            
            cumulative = 0
            business_growth = 1.0
            
            for year in range(timeline_years + 1):
                if year == 0:
                    annual_emissions = current_emissions
                else:
                    # Apply net growth rate
                    annual_emissions = current_emissions * ((1 + net_growth_rate) ** year)
                
                business_growth *= (1 + growth_rate)
                emission_intensity = annual_emissions / business_growth
                cumulative += annual_emissions
                
                projections['emissions'].append(float(annual_emissions))
                projections['cumulative_emissions'].append(float(cumulative))
                projections['emission_intensity'].append(float(emission_intensity))
            
            # Calculate summary statistics
            projections['summary'] = {
                'total_cumulative': float(cumulative),
                'final_year_emissions': float(projections['emissions'][-1]),
                'average_annual_emissions': float(np.mean(projections['emissions'])),
                'emission_change_total': float(
                    (projections['emissions'][-1] - projections['emissions'][0]) / 
                    projections['emissions'][0] * 100
                ),
                'peak_year': int(np.argmax(projections['emissions'])),
                'peak_emissions': float(max(projections['emissions']))
            }
            
            return projections
            
        except Exception as e:
            logger.error(f"Error projecting emissions: {e}")
            raise
    
    def _validate_interventions(self, interventions: List[Dict]) -> List[Dict]:
        """Validate and standardize intervention definitions"""
        try:
            validated = []
            
            for intervention in interventions:
                validated_intervention = {
                    'name': intervention.get('name', 'Unnamed Intervention'),
                    'type': intervention.get('type', 'efficiency'),
                    'start_year': intervention.get('start_year', datetime.now().year + 1),
                    'implementation_duration': intervention.get('implementation_duration', 1),
                    'annual_reduction': intervention.get('annual_reduction', 0),
                    'one_time_reduction': intervention.get('one_time_reduction', 0),
                    'cost': intervention.get('cost', 0),
                    'annual_savings': intervention.get('annual_savings', 0),
                    'effectiveness_decay': intervention.get('effectiveness_decay', 0),
                    'scope': intervention.get('scope', 'all'),
                    'dependencies': intervention.get('dependencies', []),
                    'uncertainty': intervention.get('uncertainty', 0.1)
                }
                
                # Validate ranges
                validated_intervention['annual_reduction'] = max(0, min(1, validated_intervention['annual_reduction']))
                validated_intervention['one_time_reduction'] = max(0, validated_intervention['one_time_reduction'])
                validated_intervention['uncertainty'] = max(0, min(1, validated_intervention['uncertainty']))
                
                validated.append(validated_intervention)
            
            return validated
            
        except Exception as e:
            logger.error(f"Error validating interventions: {e}")
            return interventions
    
    def _project_emissions_with_interventions(self, scenario: Dict) -> Dict:
        """Project emissions including intervention effects"""
        try:
            # Start with baseline projection
            baseline_projections = self._project_emissions(scenario)
            projections = deepcopy(baseline_projections)
            
            interventions = scenario['interventions']
            timeline_years = scenario['timeline_years']
            start_year = datetime.now().year
            
            # Track intervention effects
            intervention_effects = []
            
            for intervention in interventions:
                effect = {
                    'name': intervention['name'],
                    'annual_impact': [0] * (timeline_years + 1),
                    'cumulative_impact': [0] * (timeline_years + 1),
                    'costs': [0] * (timeline_years + 1)
                }
                
                intervention_start = intervention['start_year'] - start_year
                implementation_duration = intervention['implementation_duration']
                
                for year in range(timeline_years + 1):
                    if year >= intervention_start:
                        # Calculate intervention effect
                        years_since_start = year - intervention_start
                        
                        if years_since_start < implementation_duration:
                            # During implementation - gradual ramp up
                            effectiveness = (years_since_start + 1) / implementation_duration
                        else:
                            # Post implementation - full effect with decay
                            years_post_impl = years_since_start - implementation_duration
                            decay_rate = intervention.get('effectiveness_decay', 0)
                            effectiveness = (1 - decay_rate) ** years_post_impl
                        
                        # Apply uncertainty
                        uncertainty = intervention.get('uncertainty', 0.1)
                        effectiveness *= np.random.normal(1.0, uncertainty)
                        effectiveness = max(0, min(1, effectiveness))
                        
                        # Calculate emission reduction
                        baseline_emission = baseline_projections['emissions'][year]
                        annual_reduction = intervention['annual_reduction'] * effectiveness
                        absolute_reduction = baseline_emission * annual_reduction
                        
                        # Add one-time reduction in first year
                        if years_since_start == 0:
                            absolute_reduction += intervention['one_time_reduction']
                        
                        effect['annual_impact'][year] = absolute_reduction
                        effect['cumulative_impact'][year] = (
                            effect['cumulative_impact'][year-1] + absolute_reduction if year > 0 
                            else absolute_reduction
                        )
                        
                        # Calculate costs
                        if years_since_start == 0:
                            effect['costs'][year] = intervention['cost']
                        
                        # Subtract from baseline emissions
                        projections['emissions'][year] -= absolute_reduction
                
                intervention_effects.append(effect)
            
            # Recalculate cumulative emissions
            cumulative = 0
            for i, annual in enumerate(projections['emissions']):
                cumulative += annual
                projections['cumulative_emissions'][i] = cumulative
            
            # Update summary
            projections['summary'] = {
                'total_cumulative': float(cumulative),
                'final_year_emissions': float(projections['emissions'][-1]),
                'average_annual_emissions': float(np.mean(projections['emissions'])),
                'emission_change_total': float(
                    (projections['emissions'][-1] - projections['emissions'][0]) / 
                    projections['emissions'][0] * 100
                ),
                'total_intervention_cost': float(sum(
                    sum(effect['costs']) for effect in intervention_effects
                )),
                'total_reduction_achieved': float(sum(
                    effect['cumulative_impact'][-1] for effect in intervention_effects
                ))
            }
            
            projections['intervention_effects'] = intervention_effects
            
            return projections
            
        except Exception as e:
            logger.error(f"Error projecting emissions with interventions: {e}")
            raise
    
    def _calculate_scenario_impact(self, scenario: Dict) -> Dict:
        """Calculate impact metrics for scenario vs baseline"""
        try:
            if not self.baseline_scenario:
                return {}
            
            baseline_proj = self.baseline_scenario['projections']
            scenario_proj = scenario['projections']
            
            # Total emission reduction
            baseline_total = baseline_proj['summary']['total_cumulative']
            scenario_total = scenario_proj['summary']['total_cumulative']
            total_reduction = baseline_total - scenario_total
            reduction_percentage = (total_reduction / baseline_total) * 100
            
            # Annual reductions
            annual_reductions = []
            for i in range(len(baseline_proj['emissions'])):
                reduction = baseline_proj['emissions'][i] - scenario_proj['emissions'][i]
                annual_reductions.append(float(reduction))
            
            # Cost effectiveness
            total_cost = scenario_proj['summary'].get('total_intervention_cost', 0)
            cost_per_tonne = total_cost / total_reduction if total_reduction > 0 else 0
            
            # Peak reduction year
            peak_reduction_year = int(np.argmax(annual_reductions))
            peak_reduction = max(annual_reductions)
            
            return {
                'total_emission_reduction': float(total_reduction),
                'reduction_percentage': float(reduction_percentage),
                'average_annual_reduction': float(np.mean(annual_reductions)),
                'peak_reduction': float(peak_reduction),
                'peak_reduction_year': baseline_proj['years'][peak_reduction_year],
                'total_intervention_cost': float(total_cost),
                'cost_per_tonne_co2': float(cost_per_tonne),
                'annual_reductions': annual_reductions,
                'net_present_value': self._calculate_npv(scenario),
                'payback_period': self._calculate_payback_period(scenario)
            }
            
        except Exception as e:
            logger.error(f"Error calculating scenario impact: {e}")
            return {}
    
    def _recommend_interventions_for_target(
        self,
        target_reduction: float,
        years_to_target: int,
        strategy: str
    ) -> List[Dict]:
        """Recommend interventions to achieve target reduction"""
        try:
            # Mock intervention database (in practice, this would come from your recommendation engine)
            available_interventions = [
                {
                    'name': 'LED Lighting Upgrade',
                    'annual_reduction': 0.05,
                    'cost': 50000,
                    'implementation_duration': 1,
                    'type': 'efficiency'
                },
                {
                    'name': 'Solar Panel Installation',
                    'annual_reduction': 0.15,
                    'cost': 200000,
                    'implementation_duration': 1,
                    'type': 'renewable'
                },
                {
                    'name': 'HVAC Optimization',
                    'annual_reduction': 0.08,
                    'cost': 75000,
                    'implementation_duration': 1,
                    'type': 'efficiency'
                },
                {
                    'name': 'Electric Vehicle Fleet',
                    'annual_reduction': 0.12,
                    'cost': 150000,
                    'implementation_duration': 2,
                    'type': 'transportation'
                },
                {
                    'name': 'Building Insulation',
                    'annual_reduction': 0.10,
                    'cost': 100000,
                    'implementation_duration': 1,
                    'type': 'efficiency'
                }
            ]
            
            # Sort by strategy
            if strategy == 'cost_effective':
                # Sort by cost per reduction
                available_interventions.sort(
                    key=lambda x: x['cost'] / x['annual_reduction']
                )
            elif strategy == 'high_impact':
                # Sort by annual reduction
                available_interventions.sort(
                    key=lambda x: x['annual_reduction'], reverse=True
                )
            elif strategy == 'quick_wins':
                # Sort by implementation speed and impact
                available_interventions.sort(
                    key=lambda x: x['annual_reduction'] / x['implementation_duration'], 
                    reverse=True
                )
            
            # Select interventions to meet target
            recommended = []
            cumulative_reduction = 0
            budget_used = 0
            max_budget = 1000000  # Example budget constraint
            
            for intervention in available_interventions:
                if cumulative_reduction >= target_reduction:
                    break
                
                if budget_used + intervention['cost'] <= max_budget:
                    recommended.append({
                        **intervention,
                        'start_year': datetime.now().year + len(recommended) + 1,
                        'rationale': f"Selected for {strategy} strategy"
                    })
                    cumulative_reduction += intervention['annual_reduction']
                    budget_used += intervention['cost']
            
            return recommended
            
        except Exception as e:
            logger.error(f"Error recommending interventions for target: {e}")
            return []
    
    def _calculate_npv(self, scenario: Dict, discount_rate: float = 0.05) -> float:
        """Calculate Net Present Value of scenario"""
        try:
            if 'intervention_effects' not in scenario['projections']:
                return 0.0
            
            npv = 0.0
            carbon_price = 50  # $/tonne CO2
            
            for year, (cost, reduction) in enumerate(zip(
                [sum(effect['costs'][year] for effect in scenario['projections']['intervention_effects']) 
                 for year in range(len(scenario['projections']['emissions']))],
                [sum(effect['annual_impact'][year] for effect in scenario['projections']['intervention_effects']) 
                 for year in range(len(scenario['projections']['emissions']))]
            )):
                # Calculate cash flow (savings - costs)
                savings = reduction * carbon_price
                cash_flow = savings - cost
                
                # Discount to present value
                pv = cash_flow / ((1 + discount_rate) ** year)
                npv += pv
            
            return float(npv)
            
        except Exception as e:
            logger.error(f"Error calculating NPV: {e}")
            return 0.0
    
    def _calculate_payback_period(self, scenario: Dict) -> float:
        """Calculate payback period in years"""
        try:
            if 'intervention_effects' not in scenario['projections']:
                return float('inf')
            
            total_cost = scenario['projections']['summary'].get('total_intervention_cost', 0)
            carbon_price = 50  # $/tonne CO2
            
            cumulative_savings = 0
            
            for year, reduction in enumerate([
                sum(effect['annual_impact'][year] for effect in scenario['projections']['intervention_effects']) 
                for year in range(len(scenario['projections']['emissions']))
            ]):
                annual_savings = reduction * carbon_price
                cumulative_savings += annual_savings
                
                if cumulative_savings >= total_cost:
                    return float(year)
            
            return float('inf')
            
        except Exception as e:
            logger.error(f"Error calculating payback period: {e}")
            return float('inf')
    
    def compare_scenarios(self, scenario_names: List[str] = None) -> Dict:
        """Compare multiple scenarios"""
        try:
            if scenario_names is None:
                scenario_names = list(self.scenarios.keys())
            
            if self.baseline_scenario:
                scenarios_to_compare = {'baseline': self.baseline_scenario}
                scenarios_to_compare.update({
                    name: scenario for name, scenario in self.scenarios.items() 
                    if name in scenario_names
                })
            else:
                scenarios_to_compare = {
                    name: scenario for name, scenario in self.scenarios.items() 
                    if name in scenario_names
                }
            
            comparison = {
                'scenarios_compared': list(scenarios_to_compare.keys()),
                'comparison_metrics': {},
                'best_scenario': {},
                'trade_offs': [],
                'comparison_charts': {}
            }
            
            # Extract key metrics for each scenario
            for name, scenario in scenarios_to_compare.items():
                if name == 'baseline':
                    metrics = {
                        'total_emissions': scenario['projections']['summary']['total_cumulative'],
                        'final_year_emissions': scenario['projections']['summary']['final_year_emissions'],
                        'total_cost': 0,
                        'emission_reduction': 0,
                        'cost_per_tonne': 0,
                        'npv': 0
                    }
                else:
                    impact = scenario.get('impact_metrics', {})
                    metrics = {
                        'total_emissions': scenario['projections']['summary']['total_cumulative'],
                        'final_year_emissions': scenario['projections']['summary']['final_year_emissions'],
                        'total_cost': scenario['projections']['summary'].get('total_intervention_cost', 0),
                        'emission_reduction': impact.get('total_emission_reduction', 0),
                        'cost_per_tonne': impact.get('cost_per_tonne_co2', 0),
                        'npv': impact.get('net_present_value', 0)
                    }
                
                comparison['comparison_metrics'][name] = metrics
            
            # Find best scenarios for different criteria
            if len(scenarios_to_compare) > 1:
                non_baseline_scenarios = {
                    k: v for k, v in comparison['comparison_metrics'].items() 
                    if k != 'baseline'
                }
                
                if non_baseline_scenarios:
                    comparison['best_scenario'] = {
                        'highest_reduction': max(
                            non_baseline_scenarios.items(), 
                            key=lambda x: x[1]['emission_reduction']
                        )[0],
                        'most_cost_effective': min(
                            non_baseline_scenarios.items(), 
                            key=lambda x: x[1]['cost_per_tonne'] if x[1]['cost_per_tonne'] > 0 else float('inf')
                        )[0],
                        'highest_npv': max(
                            non_baseline_scenarios.items(), 
                            key=lambda x: x[1]['npv']
                        )[0]
                    }
            
            # Generate trade-off analysis
            comparison['trade_offs'] = self._analyze_trade_offs(comparison['comparison_metrics'])
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing scenarios: {e}")
            raise
    
    def _analyze_trade_offs(self, metrics: Dict) -> List[str]:
        """Analyze trade-offs between scenarios"""
        try:
            trade_offs = []
            
            # Compare cost vs reduction
            scenarios = [(name, data) for name, data in metrics.items() if name != 'baseline']
            
            if len(scenarios) >= 2:
                # Sort by emission reduction
                by_reduction = sorted(scenarios, key=lambda x: x[1]['emission_reduction'], reverse=True)
                # Sort by cost
                by_cost = sorted(scenarios, key=lambda x: x[1]['total_cost'])
                
                if by_reduction[0][0] != by_cost[0][0]:
                    trade_offs.append(
                        f"{by_reduction[0][0]} achieves highest reduction but at higher cost than {by_cost[0][0]}"
                    )
                
                # Compare cost effectiveness
                cost_effective = [s for s in scenarios if s[1]['cost_per_tonne'] > 0]
                if cost_effective:
                    most_efficient = min(cost_effective, key=lambda x: x[1]['cost_per_tonne'])
                    trade_offs.append(
                        f"{most_efficient[0]} offers best cost per tonne CO2 at ${most_efficient[1]['cost_per_tonne']:.2f}"
                    )
                
                # NPV analysis
                positive_npv = [s for s in scenarios if s[1]['npv'] > 0]
                if positive_npv:
                    best_npv = max(positive_npv, key=lambda x: x[1]['npv'])
                    trade_offs.append(
                        f"{best_npv[0]} offers best financial return with NPV of ${best_npv[1]['npv']:,.2f}"
                    )
            
            return trade_offs
            
        except Exception as e:
            logger.error(f"Error analyzing trade-offs: {e}")
            return []
