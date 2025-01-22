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
        """
        :param weight_data_path: Path to a JSON file containing the "mythic_weights" structure.
        """
        self.weight_data_path = weight_data_path
        self.weight_data = self._load_weight_data()

    def _load_weight_data(self) -> Dict:
        """
        Load the JSON data from disk. If error, returns an empty dict.
        """
        try:
            with open(self.weight_data_path, "r") as file:
                return json.load(file)
        except Exception as error:
            print(f"Error loading weight data: {error}")
            return {}

    def calculate_mythic_weight(self, target: str, user_inputs: List[float]) -> Optional[WeightResult]:
        """
        Calculate mythic item weights based on user inputs. 
        Essentially replicates your 'mythic_weigh' logic in an OOP method.

        :param target: Name of the item you want to weigh (case-insensitive).
        :param user_inputs: The rolled stats (or user-provided stats) to multiply by weighting factors.
        :return: WeightResult or None if not found.
        """
        data = self.weight_data.get("Data", {})
        timestamp = self.weight_data.get("latest", {}).get("Timestamp", "")
        product_main = []

        for item_name, scales in data.items():
            if target.lower() == item_name.lower():
                result_scales = {}
                for scale, stats_dict in scales.items():
                    item_weights = [float(v)/100 for k, v in stats_dict.items()]
                    product = [x * y for x, y in zip(user_inputs, item_weights)]
                    if scale == "Main":
                        product_main = product
                    result_scales[scale] = round(sum(product), 2)

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
        Get detailed scale information for an item (similar to `weigh_scale`).
        
        :param target: Name of the item (case-insensitive).
        :return: (scale_display, timestamp, scale_data, item_name) or None.
        """
        data = self.weight_data.get("Data", {})
        timestamp = self.weight_data.get("latest", {}).get("Timestamp", "")

        for item_name, scales in data.items():
            if target.lower() == item_name.lower():
                scale_display = {item_name: {}}
                scale_data = scales.get("Main", {})
                index = 1

                for scale, stats_dict in scales.items():
                    scale_content = ""
                    for stat_id, val in stats_dict.items():
                        scale_content += f"{index}. {stat_id}: {val}%\n"
                        index += 1
                    scale_display[item_name][scale] = scale_content
                    index = 1

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

