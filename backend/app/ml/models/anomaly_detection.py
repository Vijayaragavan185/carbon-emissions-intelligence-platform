import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EmissionAnomalyDetector:
    """Detect anomalies in emission data for quality assurance"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.thresholds = {}
        self.is_trained = False
        
    def prepare_features(self, emission_data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for anomaly detection"""
        try:
            features = pd.DataFrame()
            
            # Basic emission metrics
            if 'emissions' in emission_data.columns:
                features['emissions'] = emission_data['emissions']
                features['emissions_log'] = np.log1p(emission_data['emissions'])
                
            # Time-based features
            if 'date' in emission_data.columns:
                emission_data['date'] = pd.to_datetime(emission_data['date'])
                features['day_of_week'] = emission_data['date'].dt.dayofweek
                features['month'] = emission_data['date'].dt.month
                features['hour'] = emission_data['date'].dt.hour
            
            # Rolling statistics
            if 'emissions' in emission_data.columns:
                for window in [7, 30]:
                    features[f'rolling_mean_{window}'] = (
                        emission_data['emissions'].rolling(window=window).mean()
                    )
                    features[f'rolling_std_{window}'] = (
                        emission_data['emissions'].rolling(window=window).std()
                    )
                    features[f'deviation_from_mean_{window}'] = (
                        emission_data['emissions'] - features[f'rolling_mean_{window}']
                    )
            
            # Company/source features if available
            if 'company_id' in emission_data.columns:
                features['company_id'] = emission_data['company_id']
            
            if 'scope' in emission_data.columns:
                # Encode scope as numeric
                scope_mapping = {'SCOPE_1': 1, 'SCOPE_2': 2, 'SCOPE_3': 3}
                features['scope_numeric'] = emission_data['scope'].map(scope_mapping).fillna(0)
            
            # Remove NaN values
            features = features.fillna(features.mean())
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            raise
    
    def train_isolation_forest(self, features: pd.DataFrame) -> Dict:
        """Train Isolation Forest for anomaly detection"""
        try:
            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Train Isolation Forest
            iso_forest = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )
            
            # Fit model
            iso_forest.fit(features_scaled)
            
            # Predict anomalies on training data
            predictions = iso_forest.predict(features_scaled)
            anomaly_scores = iso_forest.decision_function(features_scaled)
            
            # Convert predictions (-1 for anomaly, 1 for normal)
            is_anomaly = predictions == -1
            
            # Calculate metrics
            anomaly_rate = np.mean(is_anomaly)
            threshold = np.percentile(anomaly_scores, 10)  # 10th percentile as threshold
            
            return {
                'model': iso_forest,
                'scaler': scaler,
                'anomaly_rate': float(anomaly_rate),
                'threshold': float(threshold),
                'anomaly_scores': anomaly_scores.tolist(),
                'predictions': predictions.tolist(),
                'num_anomalies': int(np.sum(is_anomaly))
            }
            
        except Exception as e:
            logger.error(f"Error training Isolation Forest: {e}")
            raise
    
    def train_statistical_detector(self, features: pd.DataFrame) -> Dict:
        """Train statistical anomaly detector using Z-score and IQR"""
        try:
            anomalies = {}
            
            for column in features.select_dtypes(include=[np.number]).columns:
                data = features[column].dropna()
                
                # Z-score method
                z_scores = np.abs((data - data.mean()) / data.std())
                z_anomalies = z_scores > 3  # 3 standard deviations
                
                # IQR method
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                iqr_anomalies = (data < lower_bound) | (data > upper_bound)
                
                # Combine methods
                combined_anomalies = z_anomalies | iqr_anomalies
                
                anomalies[column] = {
                    'z_score_anomalies': z_anomalies.tolist(),
                    'iqr_anomalies': iqr_anomalies.tolist(),
                    'combined_anomalies': combined_anomalies.tolist(),
                    'anomaly_rate': float(np.mean(combined_anomalies)),
                    'thresholds': {
                        'z_score': 3.0,
                        'iqr_lower': float(lower_bound),
                        'iqr_upper': float(upper_bound)
                    }
                }
            
            return {
                'method': 'statistical',
                'column_anomalies': anomalies,
                'overall_anomaly_rate': float(np.mean([
                    info['anomaly_rate'] for info in anomalies.values()
                ]))
            }
            
        except Exception as e:
            logger.error(f"Error training statistical detector: {e}")
            raise
    
    def train_time_series_detector(self, emission_data: pd.DataFrame) -> Dict:
        """Detect anomalies in time series patterns"""
        try:
            if 'date' not in emission_data.columns or 'emissions' not in emission_data.columns:
                raise ValueError("Data must contain 'date' and 'emissions' columns")
            
            # Prepare time series
            emission_data['date'] = pd.to_datetime(emission_data['date'])
            emission_data = emission_data.sort_values('date')
            emission_data.set_index('date', inplace=True)
            
            emissions = emission_data['emissions']
            
            # Detect level shifts
            rolling_mean = emissions.rolling(window=30).mean()
            rolling_std = emissions.rolling(window=30).std()
            
            # Points outside 2 standard deviations from rolling mean
            level_anomalies = np.abs(emissions - rolling_mean) > (2 * rolling_std)
            
            # Detect trend changes
            rolling_trend = emissions.rolling(window=14).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0]
            )
            trend_changes = np.abs(rolling_trend.diff()) > rolling_trend.std()
            
            # Detect seasonal anomalies
            monthly_means = emissions.groupby(emissions.index.month).mean()
            monthly_stds = emissions.groupby(emissions.index.month).std()
            
            expected_values = emissions.index.map(
                lambda x: monthly_means[x.month]
            )
            expected_stds = emissions.index.map(
                lambda x: monthly_stds[x.month]
            )
            
            seasonal_anomalies = np.abs(emissions - expected_values) > (2 * expected_stds)
            
            # Combine all anomaly types
            combined_anomalies = level_anomalies | trend_changes.fillna(False) | seasonal_anomalies
            
            return {
                'method': 'time_series',
                'level_anomalies': level_anomalies.tolist(),
                'trend_anomalies': trend_changes.fillna(False).tolist(),
                'seasonal_anomalies': seasonal_anomalies.tolist(),
                'combined_anomalies': combined_anomalies.tolist(),
                'anomaly_dates': emissions[combined_anomalies].index.strftime('%Y-%m-%d').tolist(),
                'anomaly_rate': float(np.mean(combined_anomalies)),
                'num_anomalies': int(np.sum(combined_anomalies))
            }
            
        except Exception as e:
            logger.error(f"Error in time series anomaly detection: {e}")
            raise
    
    def train_all_detectors(self, emission_data: pd.DataFrame) -> Dict:
        """Train all anomaly detection methods"""
        try:
            # Prepare features
            features = self.prepare_features(emission_data)
            
            results = {}
            
            # Train Isolation Forest
            logger.info("Training Isolation Forest detector...")
            iso_result = self.train_isolation_forest(features)
            results['isolation_forest'] = iso_result
            
            # Train statistical detector
            logger.info("Training statistical detector...")
            stat_result = self.train_statistical_detector(features)
            results['statistical'] = stat_result
            
            # Train time series detector
            logger.info("Training time series detector...")
            ts_result = self.train_time_series_detector(emission_data.copy())
            results['time_series'] = ts_result
            
            # Store models
            self.models = results
            self.is_trained = True
            
            # Generate summary
            summary = self._generate_detection_summary(results)
            
            return {
                'detectors': results,
                'summary': summary,
                'training_completed': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error training anomaly detectors: {e}")
            raise
    
    def detect_anomalies(self, new_data: pd.DataFrame) -> Dict:
        """Detect anomalies in new emission data"""
        if not self.is_trained:
            raise ValueError("Detectors must be trained before detecting anomalies")
        
        try:
            # Prepare features
            features = self.prepare_features(new_data)
            
            results = {}
            
            # Isolation Forest detection
            if 'isolation_forest' in self.models:
                iso_model = self.models['isolation_forest']['model']
                scaler = self.models['isolation_forest']['scaler']
                
                features_scaled = scaler.transform(features)
                predictions = iso_model.predict(features_scaled)
                scores = iso_model.decision_function(features_scaled)
                
                results['isolation_forest'] = {
                    'predictions': predictions.tolist(),
                    'anomaly_scores': scores.tolist(),
                    'is_anomaly': (predictions == -1).tolist(),
                    'num_anomalies': int(np.sum(predictions == -1))
                }
            
            # Statistical detection
            if 'statistical' in self.models:
                stat_anomalies = []
                for column in features.select_dtypes(include=[np.number]).columns:
                    if column in self.models['statistical']['column_anomalies']:
                        thresholds = self.models['statistical']['column_anomalies'][column]['thresholds']
                        data = features[column]
                        
                        # Z-score
                        z_scores = np.abs((data - data.mean()) / data.std())
                        z_anomalies = z_scores > thresholds['z_score']
                        
                        # IQR
                        iqr_anomalies = (
                            (data < thresholds['iqr_lower']) | 
                            (data > thresholds['iqr_upper'])
                        )
                        
                        combined = z_anomalies | iqr_anomalies
                        stat_anomalies.append(combined)
                
                if stat_anomalies:
                    combined_stat = np.any(stat_anomalies, axis=0)
                    results['statistical'] = {
                        'is_anomaly': combined_stat.tolist(),
                        'num_anomalies': int(np.sum(combined_stat))
                    }
            
            # Combine results
            if results:
                # Take union of all anomaly detections
                all_anomalies = []
                for method_result in results.values():
                    if 'is_anomaly' in method_result:
                        all_anomalies.append(method_result['is_anomaly'])
                
                if all_anomalies:
                    combined_anomalies = np.any(all_anomalies, axis=0)
                    
                    # Find anomalous records
                    anomaly_indices = np.where(combined_anomalies)[0]
                    anomalous_records = []
                    
                    for idx in anomaly_indices:
                        record = {
                            'index': int(idx),
                            'detected_by': []
                        }
                        
                        # Add data from original dataframe
                        if idx < len(new_data):
                            for col in new_data.columns:
                                record[col] = new_data.iloc[idx][col]
                        
                        # Check which methods detected this anomaly
                        for method, method_result in results.items():
                            if 'is_anomaly' in method_result and method_result['is_anomaly'][idx]:
                                record['detected_by'].append(method)
                        
                        anomalous_records.append(record)
                    
                    final_results = {
                        'anomalous_records': anomalous_records,
                        'total_anomalies': len(anomaly_indices),
                        'anomaly_rate': float(len(anomaly_indices) / len(new_data)),
                        'detection_methods': results,
                        'detection_timestamp': datetime.now().isoformat()
                    }
                    
                    return final_results
            
            return {
                'anomalous_records': [],
                'total_anomalies': 0,
                'anomaly_rate': 0.0,
                'message': 'No anomalies detected'
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise
    
    def _generate_detection_summary(self, results: Dict) -> Dict:
        """Generate summary of anomaly detection results"""
        summary = {
            'total_methods': len(results),
            'methods_trained': list(results.keys()),
            'anomaly_rates': {}
        }
        
        for method, result in results.items():
            if method == 'isolation_forest':
                summary['anomaly_rates'][method] = result.get('anomaly_rate', 0)
            elif method == 'statistical':
                summary['anomaly_rates'][method] = result.get('overall_anomaly_rate', 0)
            elif method == 'time_series':
                summary['anomaly_rates'][method] = result.get('anomaly_rate', 0)
        
        # Overall statistics
        if summary['anomaly_rates']:
            summary['average_anomaly_rate'] = np.mean(list(summary['anomaly_rates'].values()))
            summary['max_anomaly_rate'] = max(summary['anomaly_rates'].values())
            summary['min_anomaly_rate'] = min(summary['anomaly_rates'].values())
        
        return summary
    
    def generate_data_quality_report(self, detection_results: Dict) -> Dict:
        """Generate comprehensive data quality report"""
        try:
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'data_quality_score': 0.0,
                'issues_found': [],
                'recommendations': []
            }
            
            total_records = len(detection_results.get('anomalous_records', []))
            anomaly_rate = detection_results.get('anomaly_rate', 0)
            
            # Calculate quality score (0-100)
            quality_score = max(0, 100 - (anomaly_rate * 100))
            report['data_quality_score'] = quality_score
            
            # Classify quality level
            if quality_score >= 95:
                report['quality_level'] = 'Excellent'
            elif quality_score >= 85:
                report['quality_level'] = 'Good'
            elif quality_score >= 70:
                report['quality_level'] = 'Fair'
            else:
                report['quality_level'] = 'Poor'
            
            # Identify specific issues
            if anomaly_rate > 0.1:
                report['issues_found'].append(
                    f"High anomaly rate detected: {anomaly_rate*100:.1f}%"
                )
                report['recommendations'].append(
                    "Review data collection processes and validate anomalous records"
                )
            
            if total_records > 0:
                # Analyze anomaly patterns
                detection_methods = detection_results.get('detection_methods', {})
                
                for method, results in detection_methods.items():
                    method_anomalies = results.get('num_anomalies', 0)
                    if method_anomalies > 0:
                        report['issues_found'].append(
                            f"{method} detected {method_anomalies} anomalies"
                        )
            
            # Generate recommendations
            if not report['recommendations']:
                if quality_score >= 95:
                    report['recommendations'].append("Data quality is excellent. Continue current practices.")
                else:
                    report['recommendations'].extend([
                        "Implement automated data validation checks",
                        "Set up real-time anomaly monitoring",
                        "Review and validate flagged records"
                    ])
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating data quality report: {e}")
            raise
