#!/usr/bin/env python3
"""
Model Validation Script for Carbon Emissions ML Pipeline

This script validates all ML models and generates comprehensive reports.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
from typing import Dict, List, Any

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ml.models.forecasting import EmissionForecaster, EmissionTrendAnalyzer
from app.ml.models.optimization import CarbonReductionOptimizer
from app.ml.models.anomaly_detection import EmissionAnomalyDetector
from app.ml.models.recommendations import SustainabilityRecommendationEngine
from app.ml.models.scenario_modeling import CarbonScenarioModeler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelValidator:
    """Comprehensive model validation and reporting"""
    
    def __init__(self, output_dir: str = "validation_reports"):
        self.output_dir = output_dir
        self.validation_results = {}
        self.create_output_directory()
    
    def create_output_directory(self):
        """Create output directory for validation reports"""
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Created output directory: {self.output_dir}")
    
    def generate_test_data(self, size: str = "medium") -> Dict[str, pd.DataFrame]:
        """Generate test datasets for validation"""
        logger.info(f"Generating {size} test datasets...")
        
        sizes = {
            "small": 365,      # 1 year
            "medium": 1095,    # 3 years  
            "large": 1825      # 5 years
        }
        
        num_days = sizes.get(size, 1095)
        np.random.seed(42)
        
        # Generate realistic emission data
        dates = pd.date_range(start='2019-01-01', periods=num_days, freq='D')
        
        # Base emissions with trend and seasonality
        base_emissions = 1000
        trend = -0.1 * np.arange(num_days)  # Decreasing trend
        seasonal = 200 * np.sin(2 * np.pi * np.arange(num_days) / 365.25)
        weekly = 50 * np.sin(2 * np.pi * np.arange(num_days) / 7)
        noise = np.random.normal(0, 50, num_days)
        
        emissions = base_emissions + trend + seasonal + weekly + noise
        emissions = np.maximum(emissions, 100)  # Minimum emission level
        
        # Add some anomalies
        anomaly_indices = np.random.choice(num_days, size=int(num_days * 0.02), replace=False)
        emissions[anomaly_indices] *= np.random.uniform(2, 5, len(anomaly_indices))
        
        emission_data = pd.DataFrame({
            'date': dates,
            'emissions': emissions,
            'company_id': np.random.choice([1, 2, 3, 4, 5], num_days),
            'scope': np.random.choice(['SCOPE_1', 'SCOPE_2', 'SCOPE_3'], num_days),
            'activity_type': np.random.choice([
                'Electricity', 'Natural Gas', 'Transportation', 'Waste'
            ], num_days)
        })
        
        return {
            'emission_data': emission_data,
            'size': size,
            'num_records': num_days
        }
    
    def validate_forecasting_models(self, test_data: Dict) -> Dict:
        """Validate forecasting models"""
        logger.info("Validating forecasting models...")
        
        try:
            forecaster = EmissionForecaster()
            analyzer = EmissionTrendAnalyzer()
            
            emission_data = test_data['emission_data']
            
            # Split data for testing
            split_point = int(len(emission_data) * 0.8)
            train_data = emission_data.iloc[:split_point].copy()
            test_data_subset = emission_data.iloc[split_point:].copy()
            
            # Train models
            start_time = datetime.now()
            training_results = forecaster.train_models(train_data)
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Generate predictions
            start_time = datetime.now()
            predictions = forecaster.predict(steps=len(test_data_subset))
            prediction_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate accuracy
            predicted_values = np.array(predictions['predictions'])
            actual_values = test_data_subset['emissions'].values
            min_length = min(len(predicted_values), len(actual_values))
            
            if min_length > 0:
                from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
                
                pred_vals = predicted_values[:min_length]
                actual_vals = actual_values[:min_length]
                
                mae = mean_absolute_error(actual_vals, pred_vals)
                rmse = np.sqrt(mean_squared_error(actual_vals, pred_vals))
                mape = np.mean(np.abs((actual_vals - pred_vals) / actual_vals)) * 100
                r2 = r2_score(actual_vals, pred_vals)
            else:
                mae = rmse = mape = r2 = float('nan')
            
            # Trend analysis
            trend_analysis = analyzer.analyze_trends(emission_data.copy())
            
            results = {
                'status': 'success',
                'training_time_seconds': training_time,
                'prediction_time_seconds': prediction_time,
                'models_trained': list(training_results['models'].keys()),
                'best_model': training_results['best_model'],
                'accuracy_metrics': {
                    'mae': float(mae) if not np.isnan(mae) else None,
                    'rmse': float(rmse) if not np.isnan(rmse) else None,
                    'mape': float(mape) if not np.isnan(mape) else None,
                    'r2': float(r2) if not np.isnan(r2) else None
                },
                'trend_analysis': trend_analysis,
                'prediction_sample': predictions
            }
            
            # Validation criteria
            results['validation_passed'] = (
                training_time < 300 and  # Training should complete in 5 minutes
                prediction_time < 60 and  # Predictions should be fast
                (np.isnan(mae) or mae < 350) and  # Reasonable accuracy
                len(training_results['models']) > 0  # At least one model trained
            )
            
        except Exception as e:
            logger.error(f"Forecasting validation failed: {e}")
            results = {
                'status': 'failed',
                'error': str(e),
                'validation_passed': False
            }
        
        return results
    
    def validate_optimization_models(self) -> Dict:
        """Validate optimization models"""
        logger.info("Validating optimization models...")
        
        try:
            optimizer = CarbonReductionOptimizer()
            
            # Generate test initiatives
            initiatives = []
            for i in range(50):
                initiatives.append({
                    'name': f'Initiative_{i}',
                    'cost': np.random.uniform(10000, 500000),
                    'co2_reduction': np.random.uniform(100, 2000),
                    'category': np.random.choice(['Energy', 'Transport', 'Waste'])
                })
            
            # Define optimization problem
            start_time = datetime.now()
            problem_def = optimizer.define_reduction_problem(
                initiatives=initiatives,
                budget_constraint=2000000,
                target_reduction=10000
            )
            setup_time = (datetime.now() - start_time).total_seconds()
            
            # Run all optimization methods
            start_time = datetime.now()
            optimization_results = optimizer.run_all_optimizations()
            optimization_time = (datetime.now() - start_time).total_seconds()
            
            # Analyze results
            successful_methods = [
                method for method, result in optimization_results['optimization_results'].items()
                if result.get('success', True)
            ]
            
            results = {
                'status': 'success',
                'setup_time_seconds': setup_time,
                'optimization_time_seconds': optimization_time,
                'problem_size': len(initiatives),
                'successful_methods': successful_methods,
                'best_method': optimization_results.get('best_method'),
                'optimization_summary': optimization_results['comparison'],
                'recommendations': optimization_results['recommendations']
            }
            
            # Validation criteria
            results['validation_passed'] = (
                setup_time < 30 and  # Setup should be fast
                optimization_time < 180 and  # Optimization should complete in 3 minutes
                len(successful_methods) >= 2 and  # At least 2 methods should work
                optimization_results.get('best_method') is not None
            )
            
        except Exception as e:
            logger.error(f"Optimization validation failed: {e}")
            results = {
                'status': 'failed',
                'error': str(e),
                'validation_passed': False
            }
        
        return results
    
    def validate_anomaly_detection(self, test_data: Dict) -> Dict:
        """Validate anomaly detection models"""
        logger.info("Validating anomaly detection models...")
        
        try:
            detector = EmissionAnomalyDetector()
            emission_data = test_data['emission_data']
            
            # Train detectors
            start_time = datetime.now()
            training_results = detector.train_all_detectors(emission_data.copy())
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Test detection on new data
            test_subset = emission_data.tail(1000).copy()
            start_time = datetime.now()
            detection_results = detector.detect_anomalies(test_subset)
            detection_time = (datetime.now() - start_time).total_seconds()
            
            # Generate data quality report
            quality_report = detector.generate_data_quality_report(detection_results)
            
            results = {
                'status': 'success',
                'training_time_seconds': training_time,
                'detection_time_seconds': detection_time,
                'detectors_trained': list(training_results['detectors'].keys()),
                'anomalies_detected': detection_results['total_anomalies'],
                'anomaly_rate': detection_results['anomaly_rate'],
                'data_quality_score': quality_report['data_quality_score'],
                'quality_level': quality_report['quality_level'],
                'detection_summary': training_results['summary']
            }
            
            # Validation criteria
            results['validation_passed'] = (
                training_time < 120 and  # Training should complete in 2 minutes
                detection_time < 30 and  # Detection should be fast
                len(training_results['detectors']) >= 2 and  # Multiple detectors trained
                0 <= detection_results['anomaly_rate'] <= 1  # Valid anomaly rate
            )
            
        except Exception as e:
            logger.error(f"Anomaly detection validation failed: {e}")
            results = {
                'status': 'failed',
                'error': str(e),
                'validation_passed': False
            }
        
        return results
    
    def validate_recommendation_engine(self) -> Dict:
        """Validate recommendation engine"""
        logger.info("Validating recommendation engine...")
        
        try:
            engine = SustainabilityRecommendationEngine()
            
            # Generate test initiatives database
            initiatives = []
            for i in range(200):
                initiatives.append({
                    'id': i,
                    'name': f'Initiative_{i}',
                    'category': np.random.choice([
                        'Energy Efficiency', 'Renewable Energy', 'Transportation'
                    ]),
                    'cost_range': np.random.choice(['Low', 'Medium', 'High']),
                    'implementation_time': np.random.choice(['Short', 'Medium', 'Long']),
                    'co2_reduction_potential': np.random.uniform(100, 2000),
                    'complexity': np.random.choice(['Low', 'Medium', 'High']),
                    'industry_applicability': ['Technology', 'Manufacturing'],
                    'company_size_fit': ['Medium', 'Large']
                })
            
            # Load initiative database
            start_time = datetime.now()
            load_results = engine.load_initiative_database(initiatives)
            load_time = (datetime.now() - start_time).total_seconds()
            
            # Create test company profile
            company_data = {
                'company_id': 1,
                'industry_sector': 'Technology',
                'company_size': 'Medium',
                'annual_emissions': 5000,
                'budget_range': 'Medium',
                'current_initiatives': ['LED Lighting'],
                'emission_breakdown': {'scope1': 2000, 'scope2': 2500, 'scope3': 500}
            }
            
            company_profile = engine.create_company_profile(company_data)
            
            # Generate recommendations
            start_time = datetime.now()
            recommendations = engine.recommend_initiatives(
                company_profile=company_profile,
                num_recommendations=10
            )
            recommendation_time = (datetime.now() - start_time).total_seconds()
            
            results = {
                'status': 'success',
                'load_time_seconds': load_time,
                'recommendation_time_seconds': recommendation_time,
                'initiatives_loaded': load_results['total_initiatives'],
                'recommendations_generated': len(recommendations['recommendations']),
                'company_profile_created': company_profile is not None,
                'recommendation_sample': recommendations['recommendations'][:3] if recommendations['recommendations'] else []
            }
            
            # Validation criteria
            results['validation_passed'] = (
                load_time < 60 and  # Loading should be fast
                recommendation_time < 30 and  # Recommendations should be fast
                load_results['total_initiatives'] == 200 and  # All initiatives loaded
                len(recommendations['recommendations']) > 0  # Recommendations generated
            )
            
        except Exception as e:
            logger.error(f"Recommendation engine validation failed: {e}")
            results = {
                'status': 'failed',
                'error': str(e),
                'validation_passed': False
            }
        
        return results
    
    def validate_scenario_modeling(self) -> Dict:
        """Validate scenario modeling"""
        logger.info("Validating scenario modeling...")
        
        try:
            modeler = CarbonScenarioModeler()
            
            # Create baseline scenario
            company_data = {
                'annual_emissions': 10000,
                'emission_growth_rate': 0.02,
                'business_growth_rate': 0.05,
                'natural_efficiency': 0.01,
                'scenario_timeline': 10
            }
            
            start_time = datetime.now()
            baseline = modeler.create_baseline_scenario(company_data)
            baseline_time = (datetime.now() - start_time).total_seconds()
            
            # Create intervention scenario
            interventions = [
                {
                    'name': 'Solar Installation',
                    'start_year': 2025,
                    'annual_reduction': 0.15,
                    'cost': 200000,
                    'implementation_duration': 1
                },
                {
                    'name': 'Efficiency Upgrade',
                    'start_year': 2024,
                    'annual_reduction': 0.08,
                    'cost': 75000,
                    'implementation_duration': 1
                }
            ]
            
            start_time = datetime.now()
            intervention_scenario = modeler.create_intervention_scenario(
                'Test Scenario', interventions, 'Test intervention scenario'
            )
            intervention_time = (datetime.now() - start_time).total_seconds()
            
            # Create target scenario
            start_time = datetime.now()
            target_scenario = modeler.create_target_scenario(
                target_reduction=0.5,
                target_year=2030
            )
            target_time = (datetime.now() - start_time).total_seconds()
            
            # Compare scenarios
            start_time = datetime.now()
            comparison = modeler.compare_scenarios(['Test Scenario'])
            comparison_time = (datetime.now() - start_time).total_seconds()
            
            results = {
                'status': 'success',
                'baseline_time_seconds': baseline_time,
                'intervention_time_seconds': intervention_time,
                'target_time_seconds': target_time,
                'comparison_time_seconds': comparison_time,
                'baseline_created': baseline is not None,
                'intervention_created': intervention_scenario is not None,
                'target_created': target_scenario is not None,
                'comparison_completed': comparison is not None,
                'scenarios_in_comparison': len(comparison.get('scenarios_compared', []))
            }
            
            # Validation criteria
            results['validation_passed'] = (
                baseline_time < 30 and  # Baseline creation should be fast
                intervention_time < 60 and  # Intervention scenario creation
                target_time < 60 and  # Target scenario creation
                comparison_time < 30 and  # Comparison should be fast
                all([baseline, intervention_scenario, target_scenario, comparison])
            )
            
        except Exception as e:
            logger.error(f"Scenario modeling validation failed: {e}")
            results = {
                'status': 'failed',
                'error': str(e),
                'validation_passed': False
            }
        
        return results
    
    def run_comprehensive_validation(self, data_size: str = "medium") -> Dict:
        """Run comprehensive validation of all models"""
        logger.info("Starting comprehensive model validation...")
        
        validation_start = datetime.now()
        
        # Generate test data
        test_data = self.generate_test_data(data_size)
        
        # Validate each component
        validation_results = {
            'validation_timestamp': validation_start.isoformat(),
            'data_size': data_size,
            'test_data_info': {
                'size': test_data['size'],
                'num_records': test_data['num_records']
            },
            'forecasting': self.validate_forecasting_models(test_data),
            'optimization': self.validate_optimization_models(),
            'anomaly_detection': self.validate_anomaly_detection(test_data),
            'recommendations': self.validate_recommendation_engine(),
            'scenario_modeling': self.validate_scenario_modeling()
        }
        
        # Overall validation summary
        all_components = ['forecasting', 'optimization', 'anomaly_detection', 'recommendations', 'scenario_modeling']
        passed_components = [
            component for component in all_components
            if validation_results[component].get('validation_passed', False)
        ]
        
        validation_results['summary'] = {
            'total_components': len(all_components),
            'passed_components': len(passed_components),
            'failed_components': len(all_components) - len(passed_components),
            'success_rate': len(passed_components) / len(all_components),
            'overall_passed': len(passed_components) == len(all_components),
            'validation_duration_seconds': (datetime.now() - validation_start).total_seconds()
        }
        
        self.validation_results = validation_results
        return validation_results
    
    def generate_validation_report(self) -> str:
        """Generate human-readable validation report"""
        if not self.validation_results:
            return "No validation results available. Run validation first."
        
        results = self.validation_results
        summary = results['summary']
        
        report = f"""
# ML MODEL VALIDATION REPORT
Generated: {results['validation_timestamp']}
Data Size: {results['data_size']} ({results['test_data_info']['num_records']} records)

## OVERALL SUMMARY
✅ Components Passed: {summary['passed_components']}/{summary['total_components']}
📊 Success Rate: {summary['success_rate']:.1%}
⏱️ Total Validation Time: {summary['validation_duration_seconds']:.1f}s
🎯 Overall Status: {'PASSED' if summary['overall_passed'] else 'FAILED'}

## COMPONENT DETAILS

### 1. FORECASTING MODELS
Status: {'✅ PASSED' if results['forecasting']['validation_passed'] else '❌ FAILED'}
Training Time: {results['forecasting'].get('training_time_seconds', 'N/A')}s
Best Model: {results['forecasting'].get('best_model', 'N/A')}
Models Trained: {', '.join(results['forecasting'].get('models_trained', []))}
"""
        
        if 'accuracy_metrics' in results['forecasting']:
            metrics = results['forecasting']['accuracy_metrics']
            if metrics.get('mae'):
                report += f"MAE: {metrics['mae']:.2f}\n"
            if metrics.get('r2'):
                report += f"R²: {metrics['r2']:.3f}\n"
        
        report += f"""
### 2. OPTIMIZATION MODELS
Status: {'✅ PASSED' if results['optimization']['validation_passed'] else '❌ FAILED'}
Problem Size: {results['optimization'].get('problem_size', 'N/A')} initiatives
Optimization Time: {results['optimization'].get('optimization_time_seconds', 'N/A')}s
Successful Methods: {', '.join(results['optimization'].get('successful_methods', []))}
Best Method: {results['optimization'].get('best_method', 'N/A')}

### 3. ANOMALY DETECTION
Status: {'✅ PASSED' if results['anomaly_detection']['validation_passed'] else '❌ FAILED'}
Training Time: {results['anomaly_detection'].get('training_time_seconds', 'N/A')}s
Detectors Trained: {', '.join(results['anomaly_detection'].get('detectors_trained', []))}
Data Quality Score: {results['anomaly_detection'].get('data_quality_score', 'N/A')}
Quality Level: {results['anomaly_detection'].get('quality_level', 'N/A')}

### 4. RECOMMENDATION ENGINE
Status: {'✅ PASSED' if results['recommendations']['validation_passed'] else '❌ FAILED'}
Initiatives Loaded: {results['recommendations'].get('initiatives_loaded', 'N/A')}
Load Time: {results['recommendations'].get('load_time_seconds', 'N/A')}s
Recommendations Generated: {results['recommendations'].get('recommendations_generated', 'N/A')}

### 5. SCENARIO MODELING
Status: {'✅ PASSED' if results['scenario_modeling']['validation_passed'] else '❌ FAILED'}
Baseline Creation: {results['scenario_modeling'].get('baseline_time_seconds', 'N/A')}s
Intervention Scenario: {results['scenario_modeling'].get('intervention_time_seconds', 'N/A')}s
Target Scenario: {results['scenario_modeling'].get('target_time_seconds', 'N/A')}s

## RECOMMENDATIONS
"""
        
        # Add recommendations based on results
        if summary['overall_passed']:
            report += "🎉 All components passed validation. The ML pipeline is ready for production use.\n"
        else:
            report += "⚠️ Some components failed validation. Review the following:\n"
            
            for component in ['forecasting', 'optimization', 'anomaly_detection', 'recommendations', 'scenario_modeling']:
                if not results[component].get('validation_passed', False):
                    if results[component].get('error'):
                        report += f"- {component.title()}: {results[component]['error']}\n"
                    else:
                        report += f"- {component.title()}: Performance or accuracy issues detected\n"
        
        return report
    
    def save_results(self, filename: str = None):
        """Save validation results to files"""
        if not self.validation_results:
            logger.warning("No validation results to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON results
        json_filename = filename or f"validation_results_{timestamp}.json"
        json_path = os.path.join(self.output_dir, json_filename)
        
        with open(json_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        logger.info(f"Validation results saved to: {json_path}")
        
        # Save human-readable report
        report_filename = f"validation_report_{timestamp}.md"
        report_path = os.path.join(self.output_dir, report_filename)
        
        with open(report_path, 'w') as f:
            f.write(self.generate_validation_report())
        
        logger.info(f"Validation report saved to: {report_path}")
        
        return {
            'json_file': json_path,
            'report_file': report_path
        }

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Validate ML models for Carbon Emissions Platform')
    parser.add_argument('--data-size', choices=['small', 'medium', 'large'], 
                       default='medium', help='Size of test dataset')
    parser.add_argument('--output-dir', default='validation_reports', 
                       help='Output directory for reports')
    parser.add_argument('--save-results', action='store_true', 
                       help='Save results to files')
    
    args = parser.parse_args()
    
    # Run validation
    validator = ModelValidator(output_dir=args.output_dir)
    results = validator.run_comprehensive_validation(data_size=args.data_size)
    
    # Print summary
    print(validator.generate_validation_report())
    
    # Save results if requested
    if args.save_results:
        file_paths = validator.save_results()
        print(f"\nResults saved to:")
        print(f"JSON: {file_paths['json_file']}")
        print(f"Report: {file_paths['report_file']}")
    
    # Exit with error code if validation failed
    if not results['summary']['overall_passed']:
        sys.exit(1)

if __name__ == "__main__":
    main()
