import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ml.models.forecasting import EmissionForecaster, EmissionTrendAnalyzer
from app.ml.models.optimization import CarbonReductionOptimizer
from app.ml.models.anomaly_detection import EmissionAnomalyDetector
from app.ml.models.recommendations import SustainabilityRecommendationEngine
from app.ml.models.scenario_modeling import CarbonScenarioModeler

class TestEmissionForecaster:
    
    @pytest.fixture
    def sample_emission_data(self):
        """Create sample emission data for testing"""
        dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        emissions = 1000 + 100 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365) + np.random.normal(0, 50, len(dates))
        
        return pd.DataFrame({
            'date': dates,
            'emissions': emissions
        })
    
    @pytest.fixture
    def forecaster(self):
        return EmissionForecaster()
    
    def test_data_preparation(self, forecaster, sample_emission_data):
        """Test data preparation functionality"""
        prepared_data = forecaster.prepare_data(sample_emission_data.copy())
        
        assert not prepared_data.empty
        assert 'emissions' in prepared_data.columns
        assert prepared_data.index.name == 'date' or isinstance(prepared_data.index, pd.DatetimeIndex)
        assert not prepared_data['emissions'].isna().any()
    
    def test_feature_creation(self, forecaster, sample_emission_data):
        """Test feature creation for modeling"""
        prepared_data = forecaster.prepare_data(sample_emission_data.copy())
        emissions_series = prepared_data['emissions']
        
        features = forecaster.create_features(emissions_series)
        
        assert not features.empty
        assert 'emissions' in features.columns
        assert 'day_of_week' in features.columns
        assert 'month' in features.columns
        assert 'lag_1' in features.columns
        assert 'rolling_mean_7' in features.columns
    
    def test_model_training(self, forecaster, sample_emission_data):
        """Test model training process"""
        results = forecaster.train_models(sample_emission_data.copy())
        
        assert 'models' in results
        assert 'best_model' in results
        assert 'best_score' in results
        assert forecaster.is_trained
        assert len(results['models']) > 0
    
    def test_predictions(self, forecaster, sample_emission_data):
        """Test prediction generation"""
        # Train models first
        forecaster.train_models(sample_emission_data.copy())
        
        # Generate predictions
        predictions = forecaster.predict(steps=30)
        
        assert 'predictions' in predictions
        assert 'dates' in predictions
        assert 'model_used' in predictions
        assert 'confidence_interval' in predictions
        assert len(predictions['predictions']) == 30
        assert len(predictions['dates']) == 30
    
    def test_model_persistence(self, forecaster, sample_emission_data, tmp_path):
        """Test model saving and loading"""
        # Train models
        forecaster.train_models(sample_emission_data.copy())
        
        # Save models
        model_path = tmp_path / "test_models.joblib"
        forecaster.save_models(str(model_path))
        
        # Create new forecaster and load models
        new_forecaster = EmissionForecaster()
        new_forecaster.load_models(str(model_path))
        
        assert new_forecaster.is_trained
        assert new_forecaster.best_model == forecaster.best_model

class TestCarbonReductionOptimizer:
    
    @pytest.fixture
    def sample_initiatives(self):
        """Create sample reduction initiatives"""
        return [
            {
                'name': 'LED Lighting',
                'cost': 50000,
                'co2_reduction': 100,
                'category': 'Energy Efficiency'
            },
            {
                'name': 'Solar Panels',
                'cost': 200000,
                'co2_reduction': 500,
                'category': 'Renewable Energy'
            },
            {
                'name': 'HVAC Upgrade',
                'cost': 75000,
                'co2_reduction': 150,
                'category': 'Energy Efficiency'
            },
            {
                'name': 'Electric Vehicles',
                'cost': 150000,
                'co2_reduction': 200,
                'category': 'Transportation'
            }
        ]
    
    @pytest.fixture
    def optimizer(self):
        return CarbonReductionOptimizer()
    
    def test_problem_definition(self, optimizer, sample_initiatives):
        """Test optimization problem definition"""
        result = optimizer.define_reduction_problem(
            initiatives=sample_initiatives,
            budget_constraint=300000,
            target_reduction=400
        )
        
        assert 'num_initiatives' in result
        assert 'total_potential_reduction' in result
        assert 'total_cost_if_all' in result
        assert 'cost_effectiveness_ratios' in result
        assert result['num_initiatives'] == 4
    
    def test_cost_effectiveness_optimization(self, optimizer, sample_initiatives):
        """Test cost-effectiveness optimization"""
        optimizer.define_reduction_problem(sample_initiatives, 300000, 400)
        
        result = optimizer.cost_effectiveness_optimization()
        
        assert 'method' in result
        assert 'selected_initiatives' in result
        assert 'total_cost' in result
        assert 'total_reduction' in result
        assert 'budget_utilization' in result
        assert result['method'] == 'cost_effectiveness'
        assert result['total_cost'] <= 300000
    
    def test_linear_programming_optimization(self, optimizer, sample_initiatives):
        """Test linear programming optimization"""
        optimizer.define_reduction_problem(sample_initiatives, 300000, 400)
        
        result = optimizer.linear_programming_optimization()
        
        assert 'method' in result
        assert 'success' in result
        assert result['method'] == 'linear_programming'
        
        if result['success']:
            assert 'selected_initiatives' in result
            assert 'total_cost' in result
            assert 'total_reduction' in result
    
    def test_genetic_algorithm_optimization(self, optimizer, sample_initiatives):
        """Test genetic algorithm optimization"""
        optimizer.define_reduction_problem(sample_initiatives, 300000, 400)
        
        result = optimizer.genetic_algorithm_optimization()
        
        assert 'method' in result
        assert 'success' in result
        assert result['method'] == 'genetic_algorithm'
        
        if result['success']:
            assert 'selected_initiatives' in result
            assert 'total_cost' in result
            assert 'total_reduction' in result
    
    def test_comprehensive_optimization(self, optimizer, sample_initiatives):
        """Test running all optimization methods"""
        optimizer.define_reduction_problem(sample_initiatives, 300000, 400)
        
        results = optimizer.run_all_optimizations()
        
        assert 'optimization_results' in results
        assert 'best_method' in results
        assert 'comparison' in results
        assert 'recommendations' in results
        
        # Check that multiple methods were run
        assert len(results['optimization_results']) >= 3

class TestEmissionAnomalyDetector:
    
    @pytest.fixture
    def sample_emission_data_with_anomalies(self):
        """Create sample emission data with anomalies"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        # Normal emissions with seasonal pattern
        normal_emissions = 1000 + 100 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365)
        normal_emissions += np.random.normal(0, 30, len(dates))
        
        # Add some anomalies
        anomaly_indices = [50, 150, 250]
        for idx in anomaly_indices:
            normal_emissions[idx] *= 3  # Triple the emission (anomaly)
        
        return pd.DataFrame({
            'date': dates,
            'emissions': normal_emissions,
            'company_id': np.random.choice([1, 2, 3], len(dates)),
            'scope': np.random.choice(['SCOPE_1', 'SCOPE_2', 'SCOPE_3'], len(dates))
        })
    
    @pytest.fixture
    def anomaly_detector(self):
        return EmissionAnomalyDetector()
    
    def test_feature_preparation(self, anomaly_detector, sample_emission_data_with_anomalies):
        """Test feature preparation for anomaly detection"""
        features = anomaly_detector.prepare_features(sample_emission_data_with_anomalies.copy())
        
        assert not features.empty
        assert 'emissions' in features.columns
        assert 'emissions_log' in features.columns
        assert 'rolling_mean_7' in features.columns
        assert not features.isna().any().any()
    
    def test_isolation_forest_training(self, anomaly_detector, sample_emission_data_with_anomalies):
        """Test Isolation Forest anomaly detection"""
        features = anomaly_detector.prepare_features(sample_emission_data_with_anomalies.copy())
        
        result = anomaly_detector.train_isolation_forest(features)
        
        assert 'model' in result
        assert 'scaler' in result
        assert 'anomaly_rate' in result
        assert 'threshold' in result
        assert 'predictions' in result
        assert 'num_anomalies' in result
        
        # Should detect some anomalies
        assert result['num_anomalies'] > 0
        assert 0 <= result['anomaly_rate'] <= 1
    
    def test_statistical_detector(self, anomaly_detector, sample_emission_data_with_anomalies):
        """Test statistical anomaly detection"""
        features = anomaly_detector.prepare_features(sample_emission_data_with_anomalies.copy())
        
        result = anomaly_detector.train_statistical_detector(features)
        
        assert 'method' in result
        assert 'column_anomalies' in result
        assert 'overall_anomaly_rate' in result
        assert result['method'] == 'statistical'
        
        # Should have analysis for emissions column
        assert 'emissions' in result['column_anomalies']
    
    def test_time_series_detector(self, anomaly_detector, sample_emission_data_with_anomalies):
        """Test time series anomaly detection"""
        result = anomaly_detector.train_time_series_detector(sample_emission_data_with_anomalies.copy())
        
        assert 'method' in result
        assert 'level_anomalies' in result
        assert 'trend_anomalies' in result
        assert 'seasonal_anomalies' in result
        assert 'combined_anomalies' in result
        assert 'anomaly_dates' in result
        assert 'anomaly_rate' in result
        assert result['method'] == 'time_series'
    
    def test_comprehensive_detection(self, anomaly_detector, sample_emission_data_with_anomalies):
        """Test training all detectors"""
        results = anomaly_detector.train_all_detectors(sample_emission_data_with_anomalies.copy())
        
        assert 'detectors' in results
        assert 'summary' in results
        assert anomaly_detector.is_trained
        
        # Should have multiple detection methods
        assert 'isolation_forest' in results['detectors']
        assert 'statistical' in results['detectors']
        assert 'time_series' in results['detectors']
    
    def test_anomaly_detection_on_new_data(self, anomaly_detector, sample_emission_data_with_anomalies):
        """Test detecting anomalies in new data"""
        # Train detectors
        anomaly_detector.train_all_detectors(sample_emission_data_with_anomalies.copy())
        
        # Create new test data with known anomalies
        new_data = sample_emission_data_with_anomalies.head(100).copy()
        new_data.loc[10, 'emissions'] *= 5  # Add obvious anomaly
        
        results = anomaly_detector.detect_anomalies(new_data)
        
        assert 'anomalous_records' in results
        assert 'total_anomalies' in results
        assert 'anomaly_rate' in results
        assert 'detection_timestamp' in results
    
    def test_data_quality_report(self, anomaly_detector, sample_emission_data_with_anomalies):
        """Test data quality report generation"""
        # Train and detect
        anomaly_detector.train_all_detectors(sample_emission_data_with_anomalies.copy())
        detection_results = anomaly_detector.detect_anomalies(sample_emission_data_with_anomalies.head(100))
        
        report = anomaly_detector.generate_data_quality_report(detection_results)
        
        assert 'report_timestamp' in report
        assert 'data_quality_score' in report
        assert 'quality_level' in report
        assert 'issues_found' in report
        assert 'recommendations' in report
        
        # Quality score should be between 0 and 100
        assert 0 <= report['data_quality_score'] <= 100

class TestSustainabilityRecommendationEngine:
    
    @pytest.fixture
    def sample_company_data(self):
        return {
            'company_id': 1,
            'industry_sector': 'Technology',
            'company_size': 'Medium',
            'annual_emissions': 5000,
            'budget_range': 'Medium',
            'current_initiatives': ['LED Lighting'],
            'emission_breakdown': {'scope1': 2000, 'scope2': 2500, 'scope3': 500},
            'reduction_targets': {'2030': 0.5},
            'has_emission_tracking': True,
            'sustainability_reporting': True
        }
    
    @pytest.fixture
    def sample_initiatives(self):
        return [
            {
                'id': 1,
                'name': 'Solar Panel Installation',
                'category': 'Renewable Energy',
                'cost_range': 'High',
                'implementation_time': 'Medium',
                'co2_reduction_potential': 1000,
                'complexity': 'Medium',
                'industry_applicability': ['Technology', 'Manufacturing'],
                'company_size_fit': ['Medium', 'Large'],
                'benefits': ['Cost savings', 'Carbon reduction'],
                'risks': ['Weather dependency']
            },
            {
                'id': 2,
                'name': 'HVAC Optimization',
                'category': 'Energy Efficiency',
                'cost_range': 'Medium',
                'implementation_time': 'Short',
                'co2_reduction_potential': 500,
                'complexity': 'Low',
                'industry_applicability': ['Technology', 'Office'],
                'company_size_fit': ['Small', 'Medium', 'Large'],
                'benefits': ['Quick implementation', 'Cost effective'],
                'risks': ['Limited impact']
            }
        ]
    
    @pytest.fixture
    def recommendation_engine(self):
        return SustainabilityRecommendationEngine()
    
    def test_company_profile_creation(self, recommendation_engine, sample_company_data):
        """Test company profile creation"""
        profile = recommendation_engine.create_company_profile(sample_company_data)
        
        assert 'company_id' in profile
        assert 'industry_sector' in profile
        assert 'sustainability_maturity' in profile
        assert 'features' in profile
        assert profile['sustainability_maturity'] in ['Starter', 'Beginner', 'Intermediate', 'Advanced']
        assert isinstance(profile['features'], np.ndarray)
    
    def test_initiative_database_loading(self, recommendation_engine, sample_initiatives):
        """Test loading initiative database"""
        result = recommendation_engine.load_initiative_database(sample_initiatives)
        
        assert 'total_initiatives' in result
        assert 'categories' in result
        assert 'cost_ranges' in result
        assert result['total_initiatives'] == 2
        assert recommendation_engine.initiatives_db is not None
        assert len(recommendation_engine.initiatives_db) == 2
    
    def test_recommendation_generation(self, recommendation_engine, sample_company_data, sample_initiatives):
        """Test generating recommendations"""
        # Setup
        profile = recommendation_engine.create_company_profile(sample_company_data)
        recommendation_engine.load_initiative_database(sample_initiatives)
        
        # Generate recommendations
        recommendations = recommendation_engine.recommend_initiatives(
            company_profile=profile,
            num_recommendations=5
        )
        
        assert 'recommendations' in recommendations
        assert 'total_considered' in recommendations
        assert 'company_profile_summary' in recommendations
        assert 'recommendation_metadata' in recommendations
        
        # Check recommendation structure
        if recommendations['recommendations']:
            rec = recommendations['recommendations'][0]
            assert 'initiative' in rec
            assert 'score' in rec
            assert 'confidence' in rec
            assert 'rationale' in rec
            assert 'estimated_impact' in rec
            assert 'implementation_roadmap' in rec

class TestCarbonScenarioModeler:
    
    @pytest.fixture
    def sample_company_data(self):
        return {
            'annual_emissions': 10000,
            'emission_growth_rate': 0.02,
            'business_growth_rate': 0.05,
            'natural_efficiency': 0.01,
            'scenario_timeline': 10
        }
    
    @pytest.fixture
    def sample_interventions(self):
        return [
            {
                'name': 'Solar Installation',
                'type': 'renewable',
                'start_year': 2025,
                'annual_reduction': 0.15,
                'cost': 200000,
                'implementation_duration': 1
            },
            {
                'name': 'Efficiency Upgrade',
                'type': 'efficiency',
                'start_year': 2024,
                'annual_reduction': 0.08,
                'cost': 75000,
                'implementation_duration': 1
            }
        ]
    
    @pytest.fixture
    def scenario_modeler(self):
        return CarbonScenarioModeler()
    
    def test_baseline_scenario_creation(self, scenario_modeler, sample_company_data):
        """Test baseline scenario creation"""
        baseline = scenario_modeler.create_baseline_scenario(sample_company_data)
        
        assert 'name' in baseline
        assert 'type' in baseline
        assert 'parameters' in baseline
        assert 'projections' in baseline
        assert baseline['type'] == 'baseline'
        assert 'emissions' in baseline['projections']
        assert 'summary' in baseline['projections']
        
        # Should have projections for timeline years
        assert len(baseline['projections']['emissions']) == sample_company_data['scenario_timeline'] + 1
    
    def test_intervention_scenario_creation(self, scenario_modeler, sample_company_data, sample_interventions):
        """Test intervention scenario creation"""
        # Create baseline first
        scenario_modeler.create_baseline_scenario(sample_company_data)
        
        # Create intervention scenario
        scenario = scenario_modeler.create_intervention_scenario(
            name='Test Intervention',
            interventions=sample_interventions,
            description='Test scenario with interventions'
        )
        
        assert 'name' in scenario
        assert 'type' in scenario
        assert 'interventions' in scenario
        assert 'projections' in scenario
        assert 'impact_metrics' in scenario
        assert scenario['type'] == 'intervention'
        assert len(scenario['interventions']) == 2
    
    def test_target_scenario_creation(self, scenario_modeler, sample_company_data):
        """Test target-based scenario creation"""
        # Create baseline first
        scenario_modeler.create_baseline_scenario(sample_company_data)
        
        # Create target scenario
        scenario = scenario_modeler.create_target_scenario(
            target_reduction=0.5,  # 50% reduction
            target_year=2030,
            optimization_strategy='cost_effective'
        )
        
        assert 'name' in scenario
        assert 'type' in scenario
        assert 'target_reduction' in scenario
        assert 'target_year' in scenario
        assert 'recommended_interventions' in scenario
        assert 'projections' in scenario
        assert 'feasibility_analysis' in scenario
        assert scenario['type'] == 'target'
        assert scenario['target_reduction'] == 0.5
    
    def test_scenario_comparison(self, scenario_modeler, sample_company_data, sample_interventions):
        """Test scenario comparison functionality"""
        # Create baseline
        scenario_modeler.create_baseline_scenario(sample_company_data)
        
        # Create multiple scenarios
        scenario1 = scenario_modeler.create_intervention_scenario(
            'Scenario 1', sample_interventions[:1], 'First scenario'
        )
        scenario2 = scenario_modeler.create_intervention_scenario(
            'Scenario 2', sample_interventions, 'Second scenario'
        )
        
        # Compare scenarios
        comparison = scenario_modeler.compare_scenarios(['Scenario 1', 'Scenario 2'])
        
        assert 'scenarios_compared' in comparison
        assert 'comparison_metrics' in comparison
        assert 'best_scenario' in comparison
        assert 'trade_offs' in comparison
        
        # Should compare the specified scenarios
        assert 'Scenario 1' in comparison['scenarios_compared']
        assert 'Scenario 2' in comparison['scenarios_compared']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
