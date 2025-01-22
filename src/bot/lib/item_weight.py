"""
Author: RawFish
Description: Handles mythic item weight calculations and analysis
"""

import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class WeightResult:
    item_name: str
    scale_weights: Dict[str, float]
    main_products: List[float]
    timestamp: str
    scale_data: Dict[str, float]

class WeightManager:
    def __init__(self, weight_data_path: str):
        self.weight_data_path = weight_data_path
        self.weight_data = self._load_weight_data()

    def _load_weight_data(self) -> Dict:
        try:
            with open(self.weight_data_path, "r", encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading weight data: {e}")
            return {}

    def calculate_mythic_weight(self, target: str, user_inputs: List[float]) -> Optional[WeightResult]:
        """
        Calculate mythic item weights based on user inputs.
        """
        data = self.weight_data.get("Data", {})
        timestamp = self.weight_data.get("latest", {}).get("Timestamp", "")

        for item_name, scales in data.items():
            if target.lower() == item_name.lower():
                result_scales = {}
                for scale, stats_dict in scales.items():
                    weights = [float(v)/100 for v in stats_dict.values()]
                    products = [x * y for x, y in zip(user_inputs, weights)]
                    result_scales[scale] = round(sum(products), 2)
                    if scale == "Main":
                        product_main = products

                return WeightResult(
                    item_name=item_name,
                    scale_weights=result_scales,
                    main_products=product_main,
                    timestamp=timestamp,
                    scale_data=scales.get("Main", {})
                )
        return None

    def get_scale_info(self, target: str) -> Optional[Tuple[Dict, str, Dict, str]]:
        """
        Get detailed scale information for an item.
        """
        data = self.weight_data.get("Data", {})
        timestamp = self.weight_data.get("latest", {}).get("Timestamp", "")

        for item_name, scales in data.items():
            if target.lower() == item_name.lower():
                scale_display = {item_name: {}}
                scale_data = scales.get("Main", {})

                for scale, stats_dict in scales.items():
                    scale_content = "\n".join(
                        f"{i}. {stat_id}: {val}%" 
                        for i, (stat_id, val) in enumerate(stats_dict.items(), 1)
                    )
                    scale_display[item_name][scale] = scale_content

                return scale_display, timestamp, scale_data, item_name
        return None

    def item_weight_output(self, item_string: str, item_map: Dict[str, Dict]) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Replicates your 'item_weight_output' logic. Decodes an item string 
        to retrieve ID stats + roll percentages, then runs them through the 
        'mythic_weights' data to produce final weighting for each scale.

        :param item_string: UTF-16 WynnTils item string.
        :param item_map: A dictionary of item data (like item_manager.item_map).
        :return: A nested dictionary of the form
            {
              "ExampleItem": {
                "Scale1": 100.0,
                "Scale2": 69.0
                ...
              }
            }
            or None if the item isn't found in the mythic_weights or decoding fails.
        """
        decoded_item = self._decode_item(item_string, item_map)
        if not decoded_item:
            return None

        keys = [k for k in decoded_item.keys() if k not in ("rate", "shiny")]
        if not keys:
            return None

        item_name = keys[0]
        item_stats = decoded_item[item_name]
        item_rate = decoded_item.get("rate", {})
        data = self.weight_data.get("Data", {})
        if item_name not in data:
            return None

        item_scales = data[item_name] 
        item_IDs = {item_name: {}}
        for scale, stats_dict in item_scales.items():
            sum_val = 0.0

            for stat_id, percent_val in stats_dict.items():
                factor = float(percent_val) / 100.0
                rating = item_rate.get(stat_id, 0.0)
                sum_val += rating * factor

            item_IDs[item_name][scale] = round(sum_val, 2)

        return item_IDs

