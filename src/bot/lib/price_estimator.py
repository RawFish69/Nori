"""
Author: RawFish
Description: Price estimation and trend analysis for item marketplace
Current issue is that the lack of data and bad data makes it reliable to perform regression. 
What I have planned is revamping the approach with RL models, so let's see how that goes. 
"""

import numpy as np
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt
from datetime import datetime
from .constants import VERSION

class PriceEstimator:
    def __init__(self, output_path):
        self.output_path = output_path

    async def estimate_price(self, item_name, weight, samples, scale, user_name):
        if item_name not in samples:
            return None
        item_data = self._process_sample_data(samples[item_name])
        estimates = self._calculate_estimates(item_data, weight)
        self._generate_plot(estimates, item_name, weight, scale, user_name)
        
        return estimates.best_estimate

    def _process_sample_data(self, raw_data):
        # Will release in future
        pass

    def _calculate_estimates(self, data, weight):
        # Will release in future
        pass

    def _generate_plot(self, estimates, item_name, weight, scale, user_name):
        # Will release in future
        pass