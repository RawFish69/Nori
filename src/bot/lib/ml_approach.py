"""
ML approaches for price prediction.
"""

import numpy as np
import json
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, WhiteKernel

from lib.item_feature_engineering import ItemFeatureEngineer, create_item_feature_vector

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not available. Neural network methods will be disabled.")

try:
    from ax import optimize
    from ax.models.torch.botorch import BotorchModel
    from ax.service.ax_client import AxClient
    from ax.service.utils.instantiation import ObjectiveProperties
    AX_AVAILABLE = True
except ImportError:
    AX_AVAILABLE = False
    print("Warning: Ax Framework not available. Bayesian optimization will be disabled.")


class PriceDataset(Dataset):
    """PyTorch dataset for price estimation."""
    
    def __init__(self, features: np.ndarray, prices: np.ndarray, scaler=None):
        self.features = features
        self.prices = prices
        
        if scaler is None:
            self.scaler = StandardScaler()
            self.features = self.scaler.fit_transform(self.features)
        else:
            self.scaler = scaler
            self.features = self.scaler.transform(self.features)
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return torch.FloatTensor(self.features[idx]), torch.FloatTensor([self.prices[idx]])


class MLPPricePredictor(nn.Module):
    """Simple MLP for price prediction."""
    
    def __init__(self, input_dim: int = 50, hidden_dims: List[int] = [128, 256, 128, 64], dropout: float = 0.2):
        super(MLPPricePredictor, self).__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class LSTMPricePredictor(nn.Module):
    """LSTM for price prediction. Probably overkill but whatever."""
    
    def __init__(self, input_dim: int = 50, hidden_dim: int = 128, num_layers: int = 2, dropout: float = 0.2):
        super(LSTMPricePredictor, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_dim, 1)
    
    def forward(self, x):
        if x.dim() == 2:
            x = x.unsqueeze(1)
        
        lstm_out, _ = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        output = self.fc(last_output)
        return output


class MLPriceModels:
    """Various ML approaches for price prediction."""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path
        self.models = {}
        self.scalers = {}
        self.feature_engineer = ItemFeatureEngineer()
    
    def prepare_data(
        self,
        items_data: List[Dict[str, Any]],
        prices: np.ndarray,
        weights: Optional[List[float]] = None,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple:
        if len(items_data) < 5:
            features = self.feature_engineer.extract_features_batch(items_data, weights)
            return features, features, prices, prices, {"n_features": features.shape[1]}
        
        features = self.feature_engineer.extract_features_batch(items_data, weights)
        y = prices
        
        if len(items_data) >= 10:
            X_train, X_test, y_train, y_test = train_test_split(
                features, y, test_size=test_size, random_state=random_state
            )
        else:
            X_train, X_test, y_train, y_test = features, features, y, y
        
        feature_info = {
            "n_features": features.shape[1],
            "feature_names": self.feature_engineer.get_feature_names()
        }
        
        return X_train, X_test, y_train, y_test, feature_info
    
    def gaussian_process_regression(
        self,
        items_data: List[Dict[str, Any]],
        prices: np.ndarray,
        target_item_data: Dict[str, Any],
        weights: Optional[List[float]] = None,
        target_weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """GP regression with uncertainty estimates."""
        X_train, X_test, y_train, y_test, feature_info = self.prepare_data(
            items_data, prices, weights
        )
        
        target_features = self.feature_engineer.extract_features_from_item_data(
            target_item_data, target_weight
        ).reshape(1, -1)
        
        kernel = RBF(length_scale=1.0) + Matern(length_scale=1.0, nu=2.5) + WhiteKernel(noise_level=0.1)
        
        gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-6,
            n_restarts_optimizer=10,
            random_state=42
        )
        
        gp.fit(X_train, y_train)
        price_pred, std_pred = gp.predict(target_features, return_std=True)
        
        y_pred_test = gp.predict(X_test)
        mse = mean_squared_error(y_test, y_pred_test)
        mae = mean_absolute_error(y_test, y_pred_test)
        r2 = r2_score(y_test, y_pred_test)
        
        return {
            "method": "Gaussian Process Regression (Full Features)",
            "prediction": float(price_pred[0]),
            "uncertainty": float(std_pred[0]),
            "mse": mse,
            "mae": mae,
            "r2": r2,
            "model": gp,
            "n_features": feature_info["n_features"]
        }
    
    def bayesian_optimization_hyperparameter_tuning(
        self,
        items_data: List[Dict[str, Any]],
        prices: np.ndarray,
        target_item_data: Dict[str, Any],
        weights: Optional[List[float]] = None,
        target_weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """Bayesian optimization for hyperparameter tuning. Might be overkill with limited data."""
        if not AX_AVAILABLE:
            return {"error": "Ax Framework not available"}
        
        X_train, X_test, y_train, y_test, feature_info = self.prepare_data(items_data, prices, weights)
        
        target_features = self.feature_engineer.extract_features_from_item_data(
            target_item_data, target_weight
        ).reshape(1, -1)
        
        def train_and_evaluate(parameters: Dict[str, float]) -> float:
            n_estimators = int(parameters.get("n_estimators", 100))
            max_depth = int(parameters.get("max_depth", 5))
            learning_rate = parameters.get("learning_rate", 0.1)
            
            model = GradientBoostingRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            
            return -r2
        
        parameters = [
            {"name": "n_estimators", "type": "range", "bounds": [50, 200]},
            {"name": "max_depth", "type": "range", "bounds": [3, 10]},
            {"name": "learning_rate", "type": "range", "bounds": [0.01, 0.3]},
        ]
        
        try:
            best_parameters, best_values, experiment, model = optimize(
                parameters=parameters,
                evaluation_function=train_and_evaluate,
                minimize=True,
                total_trials=min(20, len(X_train) // 2),
            )
            
            final_model = GradientBoostingRegressor(
                n_estimators=int(best_parameters["n_estimators"]),
                max_depth=int(best_parameters["max_depth"]),
                learning_rate=best_parameters["learning_rate"],
                random_state=42
            )
            
            final_model.fit(X_train, y_train)
            price_pred = final_model.predict(target_features)[0]
            
            y_pred_test = final_model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred_test)
            mae = mean_absolute_error(y_test, y_pred_test)
            r2 = r2_score(y_test, y_pred_test)
            
            return {
                "method": "Bayesian Optimization (Ax) - Full Features",
                "prediction": float(price_pred),
                "best_hyperparameters": best_parameters,
                "mse": mse,
                "mae": mae,
                "r2": r2,
                "model": final_model,
                "n_features": feature_info["n_features"],
                "note": "Based on research paper approaches; may overfit with limited data"
            }
        except Exception as e:
            return {"error": f"Bayesian optimization failed: {str(e)}"}
    
    def neural_network_mlp(
        self,
        items_data: List[Dict[str, Any]],
        prices: np.ndarray,
        target_item_data: Dict[str, Any],
        weights: Optional[List[float]] = None,
        target_weight: Optional[float] = None,
        epochs: int = 100
    ) -> Dict[str, Any]:
        """MLP neural network for price prediction."""
        if not TORCH_AVAILABLE:
            return {"error": "PyTorch not available"}
        
        X_train, X_test, y_train, y_test, feature_info = self.prepare_data(items_data, prices, weights)
        
        train_dataset = PriceDataset(X_train, y_train)
        test_dataset = PriceDataset(X_test, y_test, scaler=train_dataset.scaler)
        
        train_loader = DataLoader(train_dataset, batch_size=min(32, len(train_dataset)), shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=len(test_dataset), shuffle=False)
        
        input_dim = feature_info["n_features"]
        model = MLPPricePredictor(input_dim=input_dim, hidden_dims=[128, 256, 128, 64], dropout=0.2)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=10)
        
        train_losses = []
        for epoch in range(epochs):
            model.train()
            epoch_loss = 0
            
            for batch_weights, batch_prices in train_loader:
                optimizer.zero_grad()
                predictions = model(batch_weights)
                loss = criterion(predictions, batch_prices)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(train_loader)
            train_losses.append(avg_loss)
            scheduler.step(avg_loss)
            
            if epoch > 20 and len(train_losses) > 10:
                if min(train_losses[-10:]) >= min(train_losses[:-10]):
                    break
        
        model.eval()
        with torch.no_grad():
            test_predictions = []
            test_targets = []
            
            for batch_weights, batch_prices in test_loader:
                pred = model(batch_weights)
                test_predictions.extend(pred.numpy().flatten())
                test_targets.extend(batch_prices.numpy().flatten())
            
            mse = mean_squared_error(test_targets, test_predictions)
            mae = mean_absolute_error(test_targets, test_predictions)
            r2 = r2_score(test_targets, test_predictions)
            
            target_features = self.feature_engineer.extract_features_from_item_data(
                target_item_data, target_weight
            ).reshape(1, -1)
            target_features_scaled = train_dataset.scaler.transform(target_features)
            target_tensor = torch.FloatTensor(target_features_scaled)
            price_pred = model(target_tensor).item()
        
        return {
            "method": "Neural Network (MLP) - Full Features",
            "prediction": float(price_pred),
            "mse": mse,
            "mae": mae,
            "r2": r2,
            "model": model,
            "train_losses": train_losses,
            "n_features": feature_info["n_features"]
        }
    
    def neural_network_lstm(
        self,
        items_data: List[Dict[str, Any]],
        prices: np.ndarray,
        target_item_data: Dict[str, Any],
        weights: Optional[List[float]] = None,
        target_weight: Optional[float] = None,
        epochs: int = 100
    ) -> Dict[str, Any]:
        """LSTM neural network. Probably overkill for this use case."""
        if not TORCH_AVAILABLE:
            return {"error": "PyTorch not available"}
        
        X_train, X_test, y_train, y_test, feature_info = self.prepare_data(items_data, prices, weights)
        
        train_dataset = PriceDataset(X_train, y_train)
        test_dataset = PriceDataset(X_test, y_test, scaler=train_dataset.scaler)
        
        train_loader = DataLoader(train_dataset, batch_size=min(32, len(train_dataset)), shuffle=False)
        test_loader = DataLoader(test_dataset, batch_size=len(test_dataset), shuffle=False)
        
        input_dim = feature_info["n_features"]
        model = LSTMPricePredictor(input_dim=input_dim, hidden_dim=128, num_layers=2, dropout=0.2)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
        
        for epoch in range(epochs):
            model.train()
            for batch_weights, batch_prices in train_loader:
                optimizer.zero_grad()
                predictions = model(batch_weights)
                loss = criterion(predictions, batch_prices)
                loss.backward()
                optimizer.step()
        
        model.eval()
        with torch.no_grad():
            test_predictions = []
            test_targets = []
            
            for batch_weights, batch_prices in test_loader:
                pred = model(batch_weights)
                test_predictions.extend(pred.numpy().flatten())
                test_targets.extend(batch_prices.numpy().flatten())
            
            mse = mean_squared_error(test_targets, test_predictions)
            mae = mean_absolute_error(test_targets, test_predictions)
            r2 = r2_score(test_targets, test_predictions)
            
            target_features = self.feature_engineer.extract_features_from_item_data(
                target_item_data, target_weight
            ).reshape(1, -1)
            target_features_scaled = train_dataset.scaler.transform(target_features)
            target_tensor = torch.FloatTensor(target_features_scaled)
            price_pred = model(target_tensor).item()
        
        return {
            "method": "Neural Network (LSTM) - Full Features",
            "prediction": float(price_pred),
            "mse": mse,
            "mae": mae,
            "r2": r2,
            "model": model,
            "n_features": feature_info["n_features"],
            "note": "LSTM approach from time-series research; adapted for full item features"
        }
    
    def ensemble_learning(
        self,
        items_data: List[Dict[str, Any]],
        prices: np.ndarray,
        target_item_data: Dict[str, Any],
        weights: Optional[List[float]] = None,
        target_weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """Ensemble of multiple models for robust predictions."""
        X_train, X_test, y_train, y_test, feature_info = self.prepare_data(items_data, prices, weights)
        
        target_features = self.feature_engineer.extract_features_from_item_data(
            target_item_data, target_weight
        ).reshape(1, -1)
        
        rf = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        gb = GradientBoostingRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
        
        ensemble = VotingRegressor([
            ('rf', rf),
            ('gb', gb)
        ])
        
        ensemble.fit(X_train, y_train)
        price_pred = ensemble.predict(target_features)[0]
        
        y_pred_test = ensemble.predict(X_test)
        mse = mean_squared_error(y_test, y_pred_test)
        mae = mean_absolute_error(y_test, y_pred_test)
        r2 = r2_score(y_test, y_pred_test)
        
        rf_pred = rf.predict(target_features)[0]
        gb_pred = gb.predict(target_features)[0]
        
        return {
            "method": "Ensemble Learning - Full Features",
            "prediction": float(price_pred),
            "individual_predictions": {
                "random_forest": float(rf_pred),
                "gradient_boosting": float(gb_pred)
            },
            "mse": mse,
            "mae": mae,
            "r2": r2,
            "model": ensemble,
            "n_features": feature_info["n_features"]
        }
    
    def meta_learning_approach(
        self,
        items_data: List[Dict[str, Any]],
        prices: np.ndarray,
        target_item_data: Dict[str, Any],
        weights: Optional[List[float]] = None,
        target_weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """Simplified meta-learning approach. Quick adaptation to new items."""
        X_train, X_test, y_train, y_test, feature_info = self.prepare_data(items_data, prices, weights)
        
        target_features = self.feature_engineer.extract_features_from_item_data(
            target_item_data, target_weight
        ).reshape(1, -1)
        
        model = GradientBoostingRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.05,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        if len(X_train) > 5:
            recent_X = X_train[-3:]
            recent_y = y_train[-3:]
            model.fit(recent_X, recent_y)
        
        price_pred = model.predict(target_features)[0]
        
        y_pred_test = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred_test)
        mae = mean_absolute_error(y_test, y_pred_test)
        r2 = r2_score(y_test, y_pred_test)
        
        return {
            "method": "Meta-Learning (Simplified) - Full Features",
            "prediction": float(price_pred),
            "mse": mse,
            "mae": mae,
            "r2": r2,
            "model": model,
            "n_features": feature_info["n_features"],
            "note": "Simplified meta-learning inspired by research papers; full implementation would require multi-item learning"
        }
    
    def compare_all_methods(
        self,
        items_data: List[Dict[str, Any]],
        prices: np.ndarray,
        target_item_data: Dict[str, Any],
        weights: Optional[List[float]] = None,
        target_weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """Compare all methods and return best prediction."""
        results = {}
        
        try:
            results["gaussian_process"] = self.gaussian_process_regression(
                items_data, prices, target_item_data, weights, target_weight
            )
        except Exception as e:
            results["gaussian_process"] = {"error": str(e)}
        
        try:
            results["ensemble"] = self.ensemble_learning(
                items_data, prices, target_item_data, weights, target_weight
            )
        except Exception as e:
            results["ensemble"] = {"error": str(e)}
        
        if TORCH_AVAILABLE:
            try:
                results["neural_network_mlp"] = self.neural_network_mlp(
                    items_data, prices, target_item_data, weights, target_weight, epochs=50
                )
            except Exception as e:
                results["neural_network_mlp"] = {"error": str(e)}
        
        if TORCH_AVAILABLE:
            try:
                results["neural_network_lstm"] = self.neural_network_lstm(
                    items_data, prices, target_item_data, weights, target_weight, epochs=50
                )
            except Exception as e:
                results["neural_network_lstm"] = {"error": str(e)}
        
        if AX_AVAILABLE and len(items_data) >= 10:
            try:
                results["bayesian_optimization"] = self.bayesian_optimization_hyperparameter_tuning(
                    items_data, prices, target_item_data, weights, target_weight
                )
            except Exception as e:
                results["bayesian_optimization"] = {"error": str(e)}
        
        try:
            results["meta_learning"] = self.meta_learning_approach(
                items_data, prices, target_item_data, weights, target_weight
            )
        except Exception as e:
            results["meta_learning"] = {"error": str(e)}
        
        best_method = None
        best_r2 = -np.inf
        
        for method_name, result in results.items():
            if "error" not in result and "r2" in result:
                if result["r2"] > best_r2:
                    best_r2 = result["r2"]
                    best_method = method_name
        
        return {
            "all_results": results,
            "best_method": best_method,
            "best_prediction": results[best_method]["prediction"] if best_method else None,
            "comparison_summary": {
                method: {
                    "prediction": result.get("prediction"),
                    "r2": result.get("r2"),
                    "mae": result.get("mae")
                } if "error" not in result else {"error": result["error"]}
                for method, result in results.items()
            }
        }
