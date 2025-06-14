import pytest
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import psutil
import sys
import os
from unittest.mock import Mock, patch

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ml.models.forecasting import EmissionForecaster, EmissionTrendAnalyzer
from app.ml.models.optimization import CarbonReductionOptimizer
from app.ml.models.anomaly_detection import EmissionAnomalyDetector
from app.ml.models.recommendations import SustainabilityRecommendationEngine
from app.ml.models.scenario_modeling import CarbonScenarioModeler

class TestModelPerformance:
    """Test ML model performance, speed, and scalability"""
    
    @pytest.fixture
    def large_emission_dataset(self):
        """Generate large emission dataset for performance testing"""
        np.random.seed(42)
        
        # Generate 3 years of hourly data (26,280 records)
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2023, 12, 31)
        dates = pd.date_range(start=start_date, end=end_date, freq='h')
        
        # Simulate realistic emission patterns
        base_emissions = 100
        seasonal_pattern = 20 * np.sin(2 * np.pi * np.arange(len(dates)) / (365.25 * 24))
        daily_pattern = 15 * np.sin(2 * np.pi * np.arange(len(dates)) / 24)
        noise = np.random.normal(0, 10, len(dates))
        trend = 0.01 * np.arange(len(dates)) / (365.25 * 24)  # Slight upward trend
        
        emissions = base_emissions + seasonal_pattern + daily_pattern + noise + trend
        emissions = np.maximum(emissions, 0)  # Ensure non-negative
        
        return pd.DataFrame({
            'date': dates,
            'emissions': emissions,
            'company_id': np.random.choice(range(1, 11), len(dates)),  # 10 companies
            'scope': np.random.choice(['SCOPE_1', 'SCOPE_2', 'SCOPE_3'], len(dates)),
            'activity_type': np.random.choice([
                'Electricity', 'Natural Gas', 'Transportation', 'Waste', 'Water'
            ], len(dates))
        })
    
    @pytest.fixture
    def memory_monitor(self):
        """Monitor memory usage during tests"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        yield {
            'initial_memory': initial_memory,
            'process': process
        }
    
    def test_forecasting_performance_large_dataset(self, large_emission_dataset, memory_monitor):
        """Test forecasting performance with large dataset"""
        forecaster = EmissionForecaster()
        
        start_time = time.time()
        start_memory = memory_monitor['process'].memory_info().rss / 1024 / 1024
        
        # Train models
        results = forecaster.train_models(large_emission_dataset.copy())
        
        training_time = time.time() - start_time
        training_memory = memory_monitor['process'].memory_info().rss / 1024 / 1024
        memory_used = training_memory - start_memory
        
        # Performance assertions
        assert training_time < 300  # Should complete within 5 minutes
        assert memory_used < 500  # Should use less than 500MB additional memory
        assert results['best_model'] is not None
        
        # Test prediction speed
        start_time = time.time()
        predictions = forecaster.predict(steps=365)  # 1 year ahead
        prediction_time = time.time() - start_time
        
        assert prediction_time < 30  # Predictions should be fast (< 30 seconds)
        assert len(predictions['predictions']) == 365
        
        print(f"Training time: {training_time:.2f}s")
        print(f"Memory used: {memory_used:.2f}MB")
        print(f"Prediction time: {prediction_time:.2f}s")
    
    def test_optimization_scalability(self, memory_monitor):
        """Test optimization scalability with increasing problem size"""
        optimizer = CarbonReductionOptimizer()
        
        # Test different problem sizes
        problem_sizes = [10, 25, 50, 75]
        performance_results = []
        
        for size in problem_sizes:
            # Generate initiatives
            initiatives = []
            for i in range(size):
                initiatives.append({
                    'name': f'Initiative_{i}',
                    'cost': np.random.uniform(10000, 500000),
                    'co2_reduction': np.random.uniform(50, 1000),
                    'category': np.random.choice(['Energy', 'Transport', 'Waste'])
                })
            
            # Define problem
            optimizer.define_reduction_problem(
                initiatives=initiatives,
                budget_constraint=1000000,
                target_reduction=5000
            )
            
            # Test each optimization method
            methods = [
                'cost_effectiveness_optimization',
                'linear_programming_optimization',
                'genetic_algorithm_optimization'
            ]
            
            for method_name in methods:
                start_time = time.time()
                start_memory = memory_monitor['process'].memory_info().rss / 1024 / 1024
                
                try:
                    method = getattr(optimizer, method_name)
                    result = method()
                    
                    end_time = time.time()
                    end_memory = memory_monitor['process'].memory_info().rss / 1024 / 1024
                    
                    performance_results.append({
                        'problem_size': size,
                        'method': method_name,
                        'time': end_time - start_time,
                        'memory': end_memory - start_memory,
                        'success': result.get('success', True)
                    })
                    
                except Exception as e:
                    performance_results.append({
                        'problem_size': size,
                        'method': method_name,
                        'time': float('inf'),
                        'memory': float('inf'),
                        'success': False,
                        'error': str(e)
                    })
        
        # Analyze scaling behavior
        df_results = pd.DataFrame(performance_results)
        
        # All methods should handle at least 100 initiatives
        small_problems = df_results[df_results['problem_size'] <= 75]
        success_rate = small_problems['success'].mean()
        assert success_rate >= 0.75, f"Should solve 75% of problems up to 75 initiatives, got {success_rate:.1%}"
        
        # Linear programming should scale best
        lp_results = df_results[df_results['method'] == 'linear_programming_optimization']
        if not lp_results.empty:
            max_lp_time = lp_results['time'].max()
            assert max_lp_time < 60, "Linear programming should solve within 1 minute"
        
        print("\nOptimization Performance Results:")
        for _, row in df_results.iterrows():
            print(f"Size: {row['problem_size']}, Method: {row['method']}, "
                  f"Time: {row['time']:.2f}s, Success: {row['success']}")
    
    def test_anomaly_detection_throughput(self, large_emission_dataset, memory_monitor):
        """Test anomaly detection throughput and accuracy"""
        detector = EmissionAnomalyDetector()
        
        # Train on subset
        training_data = large_emission_dataset.head(10000).copy()
        
        start_time = time.time()
        training_results = detector.train_all_detectors(training_data)
        training_time = time.time() - start_time
        
        assert training_time < 120  # Training should complete within 2 minutes
        assert detector.is_trained
        
        # Test detection speed on different batch sizes
        batch_sizes = [100, 1000, 5000, 10000]
        detection_times = []
        
        for batch_size in batch_sizes:
            test_data = large_emission_dataset.tail(batch_size).copy()
            
            start_time = time.time()
            detection_results = detector.detect_anomalies(test_data)
            detection_time = time.time() - start_time
            
            detection_times.append({
                'batch_size': batch_size,
                'detection_time': detection_time,
                'throughput': batch_size / detection_time,  # records per second
                'anomalies_found': detection_results['total_anomalies']
            })
        
        # Throughput should be reasonable
        df_throughput = pd.DataFrame(detection_times)
        min_throughput = df_throughput['throughput'].min()
        assert min_throughput > 10, "Should process at least 10 records per second"
        
        print(f"\nAnomaly Detection Performance:")
        print(f"Training time: {training_time:.2f}s")
        for result in detection_times:
            print(f"Batch size: {result['batch_size']}, "
                  f"Time: {result['detection_time']:.2f}s, "
                  f"Throughput: {result['throughput']:.1f} records/s")
    
    def test_recommendation_engine_response_time(self, memory_monitor):
        """Test recommendation engine response time"""
        engine = SustainabilityRecommendationEngine()
        
        # Create large initiative database
        initiatives = []
        for i in range(1000):  # 1000 initiatives
            initiatives.append({
                'id': i,
                'name': f'Initiative_{i}',
                'category': np.random.choice([
                    'Energy Efficiency', 'Renewable Energy', 'Transportation',
                    'Waste Management', 'Water Conservation', 'Green Building'
                ]),
                'cost_range': np.random.choice(['Low', 'Medium', 'High']),
                'implementation_time': np.random.choice(['Short', 'Medium', 'Long']),
                'co2_reduction_potential': np.random.uniform(100, 2000),
                'complexity': np.random.choice(['Low', 'Medium', 'High']),
                'industry_applicability': [np.random.choice(['Technology', 'Manufacturing', 'Energy', 'All'])],
                'company_size_fit': [np.random.choice(['Small', 'Medium', 'Large', 'All'])]
            })
        
        # Load database
        start_time = time.time()
        engine.load_initiative_database(initiatives)
        load_time = time.time() - start_time
        
        assert load_time < 30  # Should load within 30 seconds
        
        # Test recommendation generation speed
        company_profile = engine.create_company_profile({
            'company_id': 1,
            'industry_sector': 'Technology',
            'company_size': 'Medium',
            'annual_emissions': 5000,
            'budget_range': 'Medium',
            'current_initiatives': []
        })
        
        # Test different recommendation counts
        for num_recs in [5, 10, 20, 50]:
            start_time = time.time()
            recommendations = engine.recommend_initiatives(
                company_profile=company_profile,
                num_recommendations=num_recs
            )
            rec_time = time.time() - start_time
            
            assert rec_time < 10  # Should generate recommendations within 10 seconds
            assert len(recommendations['recommendations']) <= num_recs
            
            print(f"Recommendations ({num_recs}): {rec_time:.2f}s")
    
    def test_scenario_modeling_complexity(self, memory_monitor):
        """Test scenario modeling with complex scenarios"""
        modeler = CarbonScenarioModeler()
        
        # Create company data
        company_data = {
            'annual_emissions': 50000,
            'emission_growth_rate': 0.03,
            'business_growth_rate': 0.07,
            'natural_efficiency': 0.02,
            'scenario_timeline': 20  # 20-year projection
        }
        
        # Create baseline
        start_time = time.time()
        baseline = modeler.create_baseline_scenario(company_data)
        baseline_time = time.time() - start_time
        
        assert baseline_time < 5  # Should create baseline quickly
        
        # Create complex intervention scenario
        interventions = []
        for i in range(50):  # 50 interventions
            interventions.append({
                'name': f'Intervention_{i}',
                'type': np.random.choice(['efficiency', 'renewable', 'process']),
                'start_year': 2024 + np.random.randint(0, 10),
                'annual_reduction': np.random.uniform(0.01, 0.1),
                'cost': np.random.uniform(50000, 500000),
                'implementation_duration': np.random.randint(1, 4),
                'effectiveness_decay': np.random.uniform(0, 0.05)
            })
        
        start_time = time.time()
        scenario = modeler.create_intervention_scenario(
            name='Complex Scenario',
            interventions=interventions,
            description='Scenario with many interventions'
        )
        scenario_time = time.time() - start_time
        
        assert scenario_time < 30  # Should handle complex scenarios within 30 seconds
        assert 'projections' in scenario
        assert 'impact_metrics' in scenario
        
        # Test scenario comparison
        start_time = time.time()
        comparison = modeler.compare_scenarios(['Complex Scenario'])
        comparison_time = time.time() - start_time
        
        assert comparison_time < 10  # Comparison should be fast
        
        print(f"Scenario modeling performance:")
        print(f"Baseline: {baseline_time:.2f}s")
        print(f"Complex scenario: {scenario_time:.2f}s")
        print(f"Comparison: {comparison_time:.2f}s")
    
    def test_memory_efficiency(self, large_emission_dataset, memory_monitor):
        """Test memory efficiency across all models"""
        initial_memory = memory_monitor['initial_memory']
        
        # Test each model's memory usage
        models_to_test = [
            ('Forecaster', EmissionForecaster()),
            ('Optimizer', CarbonReductionOptimizer()),
            ('Anomaly Detector', EmissionAnomalyDetector()),
            ('Recommendation Engine', SustainabilityRecommendationEngine()),
            ('Scenario Modeler', CarbonScenarioModeler())
        ]
        
        memory_usage = {}
        
        for model_name, model in models_to_test:
            start_memory = memory_monitor['process'].memory_info().rss / 1024 / 1024
            
            try:
                if model_name == 'Forecaster':
                    model.train_models(large_emission_dataset.head(5000).copy())
                elif model_name == 'Optimizer':
                    initiatives = [
                        {'name': f'Init_{i}', 'cost': 10000, 'co2_reduction': 100}
                        for i in range(100)
                    ]
                    model.define_reduction_problem(initiatives, 500000, 2000)
                    model.cost_effectiveness_optimization()
                elif model_name == 'Anomaly Detector':
                    model.train_all_detectors(large_emission_dataset.head(3000).copy())
                elif model_name == 'Recommendation Engine':
                    initiatives = [
                        {'id': i, 'name': f'Initiative_{i}', 'category': 'Energy',
                         'cost_range': 'Medium', 'co2_reduction_potential': 100}
                        for i in range(100)
                    ]
                    model.load_initiative_database(initiatives)
                elif model_name == 'Scenario Modeler':
                    model.create_baseline_scenario({
                        'annual_emissions': 10000, 'scenario_timeline': 10
                    })
                
                end_memory = memory_monitor['process'].memory_info().rss / 1024 / 1024
                memory_used = end_memory - start_memory
                memory_usage[model_name] = memory_used
                
                # Memory usage should be reasonable
                assert memory_used < 200, f"{model_name} uses too much memory: {memory_used}MB"
                
            except Exception as e:
                print(f"Error testing {model_name}: {e}")
                memory_usage[model_name] = float('inf')
        
        print(f"\nMemory usage by model:")
        for model_name, usage in memory_usage.items():
            print(f"{model_name}: {usage:.1f}MB")
        
        # Total memory increase should be manageable
        final_memory = memory_monitor['process'].memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        assert total_increase < 1000, f"Total memory increase too high: {total_increase}MB"
    
    def test_concurrent_model_usage(self, large_emission_dataset):
        """Test models under concurrent usage scenarios"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def test_forecasting():
            try:
                forecaster = EmissionForecaster()
                data = large_emission_dataset.head(1000).copy()
                result = forecaster.train_models(data)
                results_queue.put(('forecasting', True, None))
            except Exception as e:
                results_queue.put(('forecasting', False, str(e)))
        
        def test_optimization():
            try:
                optimizer = CarbonReductionOptimizer()
                initiatives = [
                    {'name': f'Init_{i}', 'cost': 10000, 'co2_reduction': 100}
                    for i in range(20)
                ]
                optimizer.define_reduction_problem(initiatives, 200000, 1000)
                result = optimizer.cost_effectiveness_optimization()
                results_queue.put(('optimization', True, None))
            except Exception as e:
                results_queue.put(('optimization', False, str(e)))
        
        def test_anomaly():
            try:
                detector = EmissionAnomalyDetector()
                data = large_emission_dataset.head(500).copy()
                result = detector.train_all_detectors(data)
                results_queue.put(('anomaly', True, None))
            except Exception as e:
                results_queue.put(('anomaly', False, str(e)))
        
        # Run tests concurrently
        threads = [
            threading.Thread(target=test_forecasting),
            threading.Thread(target=test_optimization),
            threading.Thread(target=test_anomaly)
        ]
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        results = {}
        while not results_queue.empty():
            test_name, success, error = results_queue.get()
            results[test_name] = {'success': success, 'error': error}
        
        # All tests should complete successfully
        assert len(results) == 3, "All concurrent tests should complete"
        for test_name, result in results.items():
            assert result['success'], f"{test_name} failed: {result['error']}"
        
        # Should complete reasonably quickly even with concurrency
        assert total_time < 180, "Concurrent execution took too long"
        
        print(f"Concurrent execution completed in {total_time:.2f}s")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
