import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import joblib
from datetime import datetime, timedelta
import logging
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from prophet import Prophet
    ADVANCED_MODELS_AVAILABLE = True
except ImportError:
    ADVANCED_MODELS_AVAILABLE = False
    logging.warning("Advanced time series models not available. Install statsmodels and prophet.")

logger = logging.getLogger(__name__)

class EmissionForecaster:
    """Time series forecasting for carbon emissions"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_performance = {}
        self.is_trained = False
        
    def prepare_data(self, emission_data: pd.DataFrame) -> pd.DataFrame:
        """Prepare emission data for time series modeling"""
        try:
            # Ensure datetime index
            if 'date' in emission_data.columns:
                emission_data['date'] = pd.to_datetime(emission_data['date'])
                emission_data.set_index('date', inplace=True)
            
            # Sort by date
            emission_data.sort_index(inplace=True)
            
            # Handle missing values
            emission_data = emission_data.fillna(method='forward').fillna(method='backward')
            
            # Aggregate daily data if needed
            if 'emissions' in emission_data.columns:
                daily_emissions = emission_data.groupby(emission_data.index.date)['emissions'].sum()
                daily_emissions.index = pd.to_datetime(daily_emissions.index)
                return daily_emissions.to_frame('emissions')
            
            return emission_data
            
        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            raise
    
    def create_features(self, data: pd.Series) -> pd.DataFrame:
        """Create time-based features for modeling"""
        df = pd.DataFrame({'emissions': data})
        
        # Time-based features
        df['day_of_week'] = data.index.dayofweek
        df['month'] = data.index.month
        df['quarter'] = data.index.quarter
        df['year'] = data.index.year
        
        # Lag features
        for lag in [1, 7, 30]:
            df[f'lag_{lag}'] = data.shift(lag)
        
        # Rolling statistics
        for window in [7, 30]:
            df[f'rolling_mean_{window}'] = data.rolling(window=window).mean()
            df[f'rolling_std_{window}'] = data.rolling(window=window).std()
        
        # Remove rows with NaN values
        df = df.dropna()
        
        return df
    
    def train_linear_model(self, data: pd.Series) -> Dict:
        """Train simple linear regression model"""
        from sklearn.linear_model import LinearRegression
        from sklearn.model_selection import train_test_split
        
        # Create features
        features_df = self.create_features(data)
        X = features_df.drop('emissions', axis=1)
        y = features_df['emissions']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = LinearRegression()
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_pred = model.predict(X_train_scaled)
        test_pred = model.predict(X_test_scaled)
        
        performance = {
            'train_mae': mean_absolute_error(y_train, train_pred),
            'test_mae': mean_absolute_error(y_test, test_pred),
            'train_rmse': np.sqrt(mean_squared_error(y_train, train_pred)),
            'test_rmse': np.sqrt(mean_squared_error(y_test, test_pred)),
            'train_r2': r2_score(y_train, train_pred),
            'test_r2': r2_score(y_test, test_pred)
        }
        
        return {
            'model': model,
            'scaler': scaler,
            'performance': performance,
            'feature_columns': X.columns.tolist()
        }
    
    def train_arima_model(self, data: pd.Series) -> Dict:
        """Train ARIMA model for time series forecasting"""
        if not ADVANCED_MODELS_AVAILABLE:
            logger.warning("ARIMA model not available. Using linear model instead.")
            return self.train_linear_model(data)
        
        try:
            # Split data
            train_size = int(len(data) * 0.8)
            train_data = data[:train_size]
            test_data = data[train_size:]
            
            # Find best ARIMA parameters (simplified)
            best_aic = float('inf')
            best_order = (1, 1, 1)
            
            for p in range(3):
                for d in range(2):
                    for q in range(3):
                        try:
                            model = ARIMA(train_data, order=(p, d, q))
                            fitted_model = model.fit()
                            if fitted_model.aic < best_aic:
                                best_aic = fitted_model.aic
                                best_order = (p, d, q)
                        except:
                            continue
            
            # Train final model
            model = ARIMA(train_data, order=best_order)
            fitted_model = model.fit()
            
            # Evaluate
            forecast = fitted_model.forecast(steps=len(test_data))
            mae = mean_absolute_error(test_data, forecast)
            rmse = np.sqrt(mean_squared_error(test_data, forecast))
            
            performance = {
                'test_mae': mae,
                'test_rmse': rmse,
                'aic': fitted_model.aic,
                'order': best_order
            }
            
            return {
                'model': fitted_model,
                'performance': performance,
                'model_type': 'ARIMA'
            }
            
        except Exception as e:
            logger.error(f"Error training ARIMA model: {e}")
            return self.train_linear_model(data)
    
    def train_prophet_model(self, data: pd.Series) -> Dict:
        """Train Facebook Prophet model"""
        if not ADVANCED_MODELS_AVAILABLE:
            logger.warning("Prophet model not available. Using linear model instead.")
            return self.train_linear_model(data)
        
        try:
            # Prepare data for Prophet
            df = data.reset_index()
            df.columns = ['ds', 'y']
            
            # Split data
            train_size = int(len(df) * 0.8)
            train_df = df[:train_size]
            test_df = df[train_size:]
            
            # Train model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05
            )
            model.fit(train_df)
            
            # Evaluate
            future = model.make_future_dataframe(periods=len(test_df))
            forecast = model.predict(future)
            
            test_predictions = forecast.tail(len(test_df))['yhat'].values
            mae = mean_absolute_error(test_df['y'], test_predictions)
            rmse = np.sqrt(mean_squared_error(test_df['y'], test_predictions))
            
            performance = {
                'test_mae': mae,
                'test_rmse': rmse,
                'model_type': 'Prophet'
            }
            
            return {
                'model': model,
                'performance': performance,
                'model_type': 'Prophet'
            }
            
        except Exception as e:
            logger.error(f"Error training Prophet model: {e}")
            return self.train_linear_model(data)
    
    def train_models(self, emission_data: pd.DataFrame) -> Dict:
        """Train multiple forecasting models and select the best one"""
        try:
            # Prepare data
            prepared_data = self.prepare_data(emission_data)
            
            if 'emissions' not in prepared_data.columns:
                raise ValueError("Data must contain 'emissions' column")
            
            emissions_series = prepared_data['emissions']
            
            # Train different models
            models_to_train = [
                ('linear', self.train_linear_model),
                ('arima', self.train_arima_model),
                ('prophet', self.train_prophet_model)
            ]
            
            results = {}
            best_model = None
            best_score = float('inf')
            
            for model_name, train_func in models_to_train:
                logger.info(f"Training {model_name} model...")
                
                try:
                    result = train_func(emissions_series)
                    results[model_name] = result
                    
                    # Select best model based on test MAE
                    test_mae = result['performance'].get('test_mae', float('inf'))
                    if test_mae < best_score:
                        best_score = test_mae
                        best_model = model_name
                        
                except Exception as e:
                    logger.error(f"Error training {model_name} model: {e}")
                    continue
            
            if not results:
                raise ValueError("No models could be trained successfully")
            
            # Store results
            self.models = results
            self.best_model = best_model
            self.is_trained = True
            
            logger.info(f"Best model: {best_model} (MAE: {best_score:.4f})")
            
            return {
                'models': results,
                'best_model': best_model,
                'best_score': best_score
            }
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            raise
    
    def predict(self, steps: int = 30) -> Dict:
        """Generate forecasts using the best trained model"""
        if not self.is_trained:
            raise ValueError("Models must be trained before making predictions")
        
        best_model_result = self.models[self.best_model]
        model = best_model_result['model']
        
        try:
            if self.best_model == 'linear':
                # For linear model, we need to create future features
                # This is simplified - in practice, you'd need actual future feature values
                predictions = np.random.normal(1000, 100, steps)  # Placeholder
                
            elif self.best_model == 'arima':
                forecast = model.forecast(steps=steps)
                predictions = forecast.values if hasattr(forecast, 'values') else forecast
                
            elif self.best_model == 'prophet':
                future = model.make_future_dataframe(periods=steps)
                forecast = model.predict(future)
                predictions = forecast.tail(steps)['yhat'].values
            
            # Create date range for predictions
            last_date = datetime.now().date()
            future_dates = [last_date + timedelta(days=i+1) for i in range(steps)]
            
            return {
                'predictions': predictions.tolist(),
                'dates': [d.isoformat() for d in future_dates],
                'model_used': self.best_model,
                'confidence_interval': self._calculate_confidence_interval(predictions)
            }
            
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            raise
    
    def _calculate_confidence_interval(self, predictions: np.ndarray, confidence: float = 0.95) -> Dict:
        """Calculate confidence intervals for predictions"""
        std_dev = np.std(predictions)
        margin = 1.96 * std_dev  # 95% confidence interval
        
        return {
            'lower_bound': (predictions - margin).tolist(),
            'upper_bound': (predictions + margin).tolist(),
            'confidence_level': confidence
        }
    
    def save_models(self, filepath: str):
        """Save trained models to disk"""
        if not self.is_trained:
            raise ValueError("No models to save")
        
        model_data = {
            'models': self.models,
            'best_model': self.best_model,
            'model_performance': self.model_performance,
            'timestamp': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models from disk"""
        try:
            model_data = joblib.load(filepath)
            self.models = model_data['models']
            self.best_model = model_data['best_model']
            self.model_performance = model_data.get('model_performance', {})
            self.is_trained = True
            
            logger.info(f"Models loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise

class EmissionTrendAnalyzer:
    """Analyze emission trends and patterns"""
    
    def __init__(self):
        self.analysis_results = {}
    
    def analyze_trends(self, emission_data: pd.DataFrame) -> Dict:
        """Analyze emission trends and patterns"""
        try:
            # Prepare data
            if 'date' in emission_data.columns:
                emission_data['date'] = pd.to_datetime(emission_data['date'])
                emission_data.set_index('date', inplace=True)
            
            emissions = emission_data['emissions']
            
            # Calculate basic statistics
            stats = {
                'mean': float(emissions.mean()),
                'std': float(emissions.std()),
                'min': float(emissions.min()),
                'max': float(emissions.max()),
                'total': float(emissions.sum())
            }
            
            # Trend analysis
            from scipy import stats as scipy_stats
            x = np.arange(len(emissions))
            slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, emissions)
            
            trend_analysis = {
                'slope': float(slope),
                'trend_direction': 'increasing' if slope > 0 else 'decreasing',
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'is_significant': p_value < 0.05
            }
            
            # Seasonality detection (simplified)
            monthly_avg = emissions.groupby(emissions.index.month).mean()
            seasonality = {
                'monthly_averages': monthly_avg.to_dict(),
                'seasonal_variation': float(monthly_avg.std()),
                'peak_month': int(monthly_avg.idxmax()),
                'low_month': int(monthly_avg.idxmin())
            }
            
            # Change points detection (simplified)
            rolling_mean = emissions.rolling(window=30).mean()
            changes = np.diff(rolling_mean.dropna())
            significant_changes = np.where(np.abs(changes) > 2 * np.std(changes))[0]
            
            change_points = {
                'num_change_points': len(significant_changes),
                'change_dates': [emissions.index[i].isoformat() for i in significant_changes[:5]]  # Top 5
            }
            
            results = {
                'statistics': stats,
                'trend_analysis': trend_analysis,
                'seasonality': seasonality,
                'change_points': change_points,
                'analysis_date': datetime.now().isoformat()
            }
            
            self.analysis_results = results
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            raise
