# backend/app/ml/model_trainer.py
import numpy as np
import pandas as pd
import lightgbm as lgb
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime
from app.ml.feature_engineering import FeatureEngineering
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class F1RacePredictor:
    """Train and manage F1 race winner prediction model."""
    
    MODEL_PATH = 'app/ml/models/f1_predictor.pkl'
    SCALER_PATH = 'app/ml/models/scaler.pkl'
    
    def __init__(self):
        self.model: Optional[lgb.Booster] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.is_trained = False
        self.last_training_time: Optional[datetime] = None
        self.training_samples = 0
    
    def generate_synthetic_training_data(self, num_races: int = 100, drivers_per_race: int = 20) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic training data for model initialization.
        In production, replace with real historical data from OpenF1 API.
        """
        logger.info(f"Generating synthetic training data: {num_races} races, {drivers_per_race} drivers/race")
        
        X_train = []
        y_train = []
        
        for race_idx in range(num_races):
            for position in range(1, drivers_per_race + 1):
                # Create synthetic driver data
                driver_data = {
                    'position': position,
                    'grid_position': np.random.randint(1, drivers_per_race + 1),
                    'gap_to_leader': position * np.random.uniform(0, 5),
                    'interval_to_ahead': np.random.uniform(0.5, 3.0),
                    'last_lap_time': 88 + np.random.normal(0, 3),
                    'best_lap_time': 85 + np.random.normal(0, 2),
                    'avg_lap_time': 87 + np.random.normal(0, 2.5),
                    'lap_consistency': np.random.uniform(1, 5),
                    'total_laps': np.random.randint(10, 56),
                    'tyre_compound': np.random.randint(1, 4),
                    'tyre_age': np.random.randint(0, 30),
                    'stints_completed': np.random.randint(1, 4)
                }
                
                feature_vector, names = FeatureEngineering.create_feature_vector(driver_data)
                X_train.append(feature_vector)
                
                # Target: 1 if driver finishes (simplified for demo)
                # In production, use actual race outcomes
                finish_probability = 1.0 - (position / drivers_per_race) * 0.3
                y_train.append(1 if np.random.random() < finish_probability else 0)
                
                if self.feature_names and not names:
                    self.feature_names = list(names)
        
        return np.array(X_train, dtype=np.float32), np.array(y_train, dtype=np.int32)
    
    def train(self, X: Optional[np.ndarray] = None, y: Optional[np.ndarray] = None) -> bool:
        """
        Train the LightGBM model.
        
        Args:
            X: Feature matrix (if None, generates synthetic data)
            y: Target labels (if None, generates synthetic data)
        
        Returns:
            True if training successful, False otherwise
        """
        try:
            # Generate synthetic data if not provided
            if X is None or y is None:
                X, y = self.generate_synthetic_training_data()
            
            logger.info(f"Training model with {X.shape[0]} samples, {X.shape[1]} features")
            
            # Get feature names if not set
            if not self.feature_names:
                self.feature_names = FeatureEngineering.get_feature_names()
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Create LightGBM datasets
            train_data = lgb.Dataset(X_train_scaled, label=y_train)
            test_data = lgb.Dataset(X_test_scaled, label=y_test, reference=train_data)
            
            # LightGBM parameters optimized for inference speed
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.8,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': 0,
                'seed': 42,
                'max_depth': 6,
                'num_threads': -1  # Use all available cores
            }
            
            # Train model
            self.model = lgb.train(
                params,
                train_data,
                num_boost_round=100,
                valid_sets=[test_data],
                valid_names=['test'],
                callbacks=[
                    lgb.early_stopping(stopping_rounds=10),
                    lgb.log_evaluation(period=0)
                ]
            )
            
            # Save model
            self.save_model()
            
            self.is_trained = True
            self.last_training_time = datetime.utcnow()
            self.training_samples = X.shape[0]
            
            logger.info("Model training completed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions on input features.
        
        Args:
            X: Feature matrix of shape (n_samples, n_features)
        
        Returns:
            Array of prediction probabilities
        """
        if self.model is None:
            logger.warning("Model not trained. Loading from disk...")
            if not self.load_model():
                raise ValueError("No trained model available")
        
        try:
            # Scale features
            if self.scaler is None:
                logger.warning("Scaler not available")
                return np.array([])
            
            X_scaled = self.scaler.transform(X)
            
            # Make predictions
            predictions = self.model.predict(X_scaled)
            
            return np.array(predictions, dtype=np.float32)
        
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            return np.array([])
    
    def predict_single(self, driver_data: Dict) -> float:
        """
        Make prediction for a single driver.
        
        Args:
            driver_data: Dictionary with driver features
        
        Returns:
            Probability score (0-1)
        """
        try:
            feature_vector, _ = FeatureEngineering.create_feature_vector(driver_data)
            feature_vector = feature_vector.reshape(1, -1)
            
            prediction = self.predict(feature_vector)
            
            if len(prediction) > 0:
                return float(prediction[0])
            return 0.0
        
        except Exception as e:
            logger.error(f"Error predicting for single driver: {str(e)}")
            return 0.0
    
    def save_model(self) -> bool:
        """Save trained model and scaler to disk."""
        try:
            os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
            
            if self.model:
                self.model.save_model(self.MODEL_PATH)
            
            if self.scaler:
                joblib.dump(self.scaler, self.SCALER_PATH)
            
            logger.info(f"Model saved to {self.MODEL_PATH}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False
    
    def load_model(self) -> bool:
        """Load trained model and scaler from disk."""
        try:
            if os.path.exists(self.MODEL_PATH):
                self.model = lgb.Booster(model_file=self.MODEL_PATH)
                logger.info(f"Model loaded from {self.MODEL_PATH}")
            else:
                logger.warning(f"Model file not found at {self.MODEL_PATH}")
                return False
            
            if os.path.exists(self.SCALER_PATH):
                self.scaler = joblib.load(self.SCALER_PATH)
                logger.info(f"Scaler loaded from {self.SCALER_PATH}")
            else:
                logger.warning(f"Scaler file not found at {self.SCALER_PATH}")
            
            self.is_trained = True
            return True
        
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the trained model."""
        if self.model is None:
            return {}
        
        try:
            importance = self.model.feature_importance()
            feature_importance_dict = {
                name: float(importance[i]) 
                for i, name in enumerate(self.feature_names)
            }
            return dict(sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True))
        
        except Exception as e:
            logger.error(f"Error getting feature importance: {str(e)}")
            return {}

# Global predictor instance
_predictor: Optional[F1RacePredictor] = None

def get_predictor() -> F1RacePredictor:
    """Get or create global predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = F1RacePredictor()
        if not _predictor.load_model():
            logger.info("Initializing new model with synthetic training data...")
            _predictor.train()
    return _predictor