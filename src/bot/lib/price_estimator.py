"""
Author: RawFish
Description: Price estimation and trend analysis for item marketplace

This module provides price estimation using various approaches:
- Traditional regression (polynomial, spline)
- Advanced ML methods (see ml_approach.py)
- Ensemble methods

Status: Proof of Concept

I've implemented proof of concept code for various price estimation methods, but we don't 
have a completed pipeline yet. The current implementation includes:
- Traditional regression methods (polynomial, spline, linear interpolation)
- Advanced ML approaches (Bayesian optimization, neural networks, ensemble learning, etc.)
- Feature engineering for full item data

However, the full integration and production pipeline is still a work in progress. This might 
be completed by me or someone else in the future. Regardless, this source code can serve as 
a reference for the approaches and methods I've explored.

Current challenges:
- Lack of sufficient data and data quality issues make reliable regression difficult
- Full ML pipeline integration needs more work
- Data collection and validation pipeline needs to be established

Future work:
- Complete the data pipeline
- Improve data quality and collection methods
- Full integration of ML methods into production
- Possibly explore RL models for dynamic pricing
"""

import numpy as np
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

from lib.constants import VERSION
from lib.ml_approach import MLPriceModels
from lib.item_feature_engineering import ItemFeatureEngineer

try:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    from sklearn.ensemble import RandomForestRegressor, DecisionTreeRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class PriceEstimator:
    """
    Main price estimator class that integrates traditional and advanced ML methods.
    """
    
    def __init__(self, output_path: Optional[Path] = None):
        self.output_path = output_path
        self.ml_models = MLPriceModels()
        self.feature_engineer = ItemFeatureEngineer()
    
    async def estimate_price(
        self,
        item_name: str,
        weight: float,
        samples: Dict[str, List],
        scale: str,
        user_name: str,
        use_advanced_ml: bool = False,
        target_item_data: Optional[Dict[str, Any]] = None,
        sample_items_data: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate price for an item using various methods.
        
        Now supports full item feature vectors including stats, rates, item type, tier, etc.
        If full item data is not provided, falls back to weight-only approach (backward compatible).
        
        Args:
            item_name: Name of the item
            weight: Weight percentage of the item
            samples: Dictionary of sample data (item_name -> list of [weight, price, timestamp])
            scale: Scale name (e.g., "Main")
            user_name: Username for file naming
            use_advanced_ml: Whether to use advanced ML methods
            target_item_data: Optional decoded item data for target item (from decode_item)
            sample_items_data: Optional list of decoded item data for samples
            
        Returns:
            Dictionary with estimation results or None if estimation fails
        """
        if item_name not in samples:
            return None
        
        item_data = self._process_sample_data(samples[item_name])
        
        if use_advanced_ml and len(item_data["weights"]) >= 5:
            # Use advanced ML models with full item features if available
            if target_item_data is not None and sample_items_data is not None:
                # Use full item features
                ml_results = self.ml_models.compare_all_methods(
                    sample_items_data,
                    item_data["prices"],
                    target_item_data,
                    list(item_data["weights"]),
                    weight
                )
            else:
                # Fallback: create minimal feature vectors from weights only
                # This maintains backward compatibility
                items_data = self._create_minimal_item_data(item_data["weights"])
                target_item_data_minimal = self._create_minimal_item_data([weight])[0]
                
                ml_results = self.ml_models.compare_all_methods(
                    items_data,
                    item_data["prices"],
                    target_item_data_minimal,
                    list(item_data["weights"]),
                    weight
                )
            
            estimates = {
                "best_estimate": ml_results["best_prediction"],
                "method": ml_results["best_method"],
                "all_methods": ml_results["comparison_summary"],
                "ml_results": ml_results
            }
        else:
            # Use traditional methods
            estimates = self._calculate_estimates_traditional(item_data, weight)
        
        # Generate plot
        plot_path = self._generate_plot(estimates, item_name, weight, scale, user_name, item_data)
        
        return {
            **estimates,
            "plot_path": plot_path,
            "item_name": item_name,
            "weight": weight,
            "scale": scale
        }
    
    def _process_sample_data(self, raw_data: List[List[float]]) -> Dict[str, np.ndarray]:
        """
        Process raw sample data into clean arrays.
        
        Args:
            raw_data: List of [weight, price, timestamp] entries
            
        Returns:
            Dictionary with processed weights and prices
        """
        if not raw_data or len(raw_data) == 0:
            return {"weights": np.array([]), "prices": np.array([])}
        
        # Filter and deduplicate data
        if len(raw_data) > 10:
            highest_weight = max(raw_data, key=lambda x: x[0])
            sorted_data = sorted(raw_data, key=lambda x: x[2], reverse=True)
            filtered_data = [highest_weight] + sorted_data[:29]
            raw_data = filtered_data
        
        # Create dictionary to keep latest price for each weight
        item_data_dict = {}
        for entry in raw_data:
            w, p, t = entry
            if w not in item_data_dict or t > item_data_dict[w][1]:
                item_data_dict[w] = (p, t)
        
        weights = np.array(list(item_data_dict.keys()))
        prices = np.array([item_data_dict[w][0] / 262144 for w in weights])  # Convert to stx
        
        return {
            "weights": weights,
            "prices": prices,
            "raw_data": raw_data
        }
    
    def _create_minimal_item_data(self, weights: List[float]) -> List[Dict[str, Any]]:
        """
        Create minimal item data dictionaries from weights only.
        
        This is used for backward compatibility when full item data is not available.
        Creates feature vectors with weight as the primary feature.
        
        Args:
            weights: List of weight values
            
        Returns:
            List of minimal item data dictionaries
        """
        items_data = []
        for w in weights:
            # Create minimal item data with just weight
            # The feature engineer expects: {item_name: {stats}, "rate": {rates}, ...}
            # For minimal data, we create a dummy structure
            # Weight will be passed separately to extract_features_from_item_data
            item_name = "dummy_item"
            item_data = {
                item_name: {},  # Empty stats dict - feature engineer will use zeros
                "rate": {},  # Empty rates dict - feature engineer will use zeros
                "item_type": "unknown",
                "item_tier": "unknown",
                "level_requirement": 0,
                "shiny": None,
                "misc": {"reroll": 0}
            }
            items_data.append(item_data)
        return items_data
    
    def _calculate_estimates_traditional(self, data: Dict[str, np.ndarray], 
                                       target_weight: float) -> Dict[str, Any]:
        """
        Calculate price estimates using traditional methods.
        
        Args:
            data: Processed data dictionary
            target_weight: Weight to predict for
            
        Returns:
            Dictionary with estimates and method information
        """
        weights = data["weights"]
        prices = data["prices"]
        
        if len(weights) < 3:
            # Not enough data
            return {
                "best_estimate": None,
                "method": "insufficient_data",
                "error": "Not enough data points for estimation"
            }
        
        # Polynomial regression
        try:
            z = np.polyfit(weights, prices, min(3, len(weights) - 1))
            p = np.poly1d(z)
            poly_estimate = p(target_weight)
        except:
            poly_estimate = None
        
        # Cubic spline
        try:
            cs = CubicSpline(weights, prices)
            spline_estimate = cs(target_weight)
        except:
            spline_estimate = None
        
        # Linear interpolation
        try:
            linear_estimate = np.interp(target_weight, weights, prices)
        except:
            linear_estimate = None
        
        # Use best available estimate
        estimates = [e for e in [spline_estimate, poly_estimate, linear_estimate] if e is not None]
        best_estimate = estimates[0] if estimates else None
        
        return {
            "best_estimate": best_estimate,
            "method": "traditional",
            "polynomial": poly_estimate,
            "spline": spline_estimate,
            "linear": linear_estimate
        }
    
    def _generate_plot(self, estimates: Dict[str, Any], item_name: str, 
                      weight: float, scale: str, user_name: str,
                      data: Dict[str, np.ndarray]) -> Optional[Path]:
        """
        Generate visualization plot for price estimation.
        
        Args:
            estimates: Estimation results
            item_name: Item name
            weight: Target weight
            scale: Scale name
            user_name: Username
            data: Processed data
            
        Returns:
            Path to saved plot or None
        """
        if self.output_path is None:
            return None
        
        try:
            weights = data["weights"]
            prices = data["prices"]
            
            fig, ax = plt.subplots(figsize=(8, 7))
            fig.patch.set_facecolor('#36393f')
            ax.set_facecolor('#36393f')
            
            # Plot data points
            errors = [p * 0.1 for p in prices]
            ax.errorbar(weights, prices, yerr=errors, fmt='bo', label="Sample Data",
                       ecolor='white', alpha=0.5, capsize=5)
            
            # Plot prediction
            if estimates.get("best_estimate"):
                ax.scatter(weight, estimates["best_estimate"], color='red', s=100, zorder=5,
                          label=f"Price Estimate ({scale} Scale)")
            
            ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray')
            ax.set_title(f"Price Estimation for {item_name}", color='white')
            ax.xaxis.label.set_color('lightgray')
            ax.yaxis.label.set_color('lightgray')
            ax.tick_params(axis='x', colors='lightgray')
            ax.tick_params(axis='y', colors='lightgray')
            
            plt.legend(loc="upper left", fontsize=12)
            plt.tight_layout()
            
            filename = self.output_path / f"pricecheck_{user_name}.png"
            plt.savefig(filename, bbox_inches='tight', facecolor='#36393f')
            plt.close()
            
            return filename
        except Exception as e:
            print(f"Error generating plot: {e}")
            return None
