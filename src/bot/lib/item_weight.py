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
        Decodes an item string to retrieve ID stats + roll percentages, then runs them through the 
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

    def _decode_item(self, item_string: str, item_map: Dict) -> Optional[Dict]:
        """Decode item string using wynntilsresolver."""
        try:
            import wynntilsresolver
            item = wynntilsresolver.item.GearItemResolver.from_utf16(item_string)
            name = item.name
            ids = item.identifications
            stats_output = {name: {}, "rate": {}, "shiny": None}
            data = item_map.get(name, {})
            id_range = data.get("identifications", {})
            if item.shiny:
                stats_output["shiny"] = f"{item.shiny.display_name}: {item.shiny.value}"
            for stat in ids:
                if stat.roll >= 0:
                    id_min = id_range.get(stat.id, {}).get("min", 0)
                    id_max = id_range.get(stat.id, {}).get("max", 0)
                    id_base = id_range.get(stat.id, {}).get("raw", 0)
                    if stat.roll > 0:
                        id_rolled = round((stat.roll / 100) * id_base, 2)
                        if abs(abs(id_rolled) - abs(int(id_rolled))) == 0.5:
                            if id_base > 0:
                                id_rolled = int(id_rolled) + 1
                            else:
                                id_rolled = int(id_rolled)
                        else:
                            id_rolled = round(id_rolled)
                    else:
                        id_rolled = stat.roll
                    if stat.base > 0:
                        if id_min != id_max:
                            percentage = (id_rolled - id_min) / (id_max - id_min) * 100
                        else:
                            percentage = 100
                    else:
                        if id_min != id_max:
                            percentage = (1 - (id_max - id_rolled) / (id_max - id_min)) * 100
                        else:
                            percentage = 100
                    stats_output[name].update({stat.id: id_rolled})
                    stats_output["rate"].update({stat.id: round(percentage, 2)})
            return stats_output
        except Exception as error:
            print(f"Decode error: {error}")
            return None


def mythic_weigh(target: str, user_input: list, weight_data_path: str = None) -> tuple:
    """Calculate mythic weight from user input percentages."""
    import json
    from lib.config import DATA_PATH
    if weight_data_path is None:
        weight_data_path = DATA_PATH / "mythic_weights.json"
    
    with open(weight_data_path, "r") as file:
        data = json.load(file)["Data"]
    
    item_weights = []
    item_name = ""
    result = {}
    product_main = []
    for item in data:
        scales = data[item]
        if target.lower() == item.lower():
            item_name = item
            result = {item: {}}
            for scale in scales:
                stats = scales[scale]
                item_weights.clear()
                for id in stats:
                    weight = float(stats[id]) / 100
                    item_weights.append(weight)
                product = list(map(lambda x, y: x * y, user_input, item_weights))
                if scale == "Main":
                    product_main = product
                weighted_overall = round(sum(product), 2)
                result[item].update({scale: weighted_overall})
    
    if item_name == "":
        return None
    
    return result, product_main


def weigh_scale(target: str, weight_data_path: str = None) -> tuple:
    """Get weighing scale for an item."""
    import json
    from lib.config import DATA_PATH
    if weight_data_path is None:
        weight_data_path = DATA_PATH / "mythic_weights.json"
    
    with open(weight_data_path, "r") as file:
        raw_data = json.load(file)
        data = raw_data["Data"]
    
    timestamp = raw_data["latest"]["Timestamp"]
    scale_data = {}
    scale_display = {}
    item_name = ""
    index = 1
    for item in data:
        if target.lower() == item.lower():
            scales = data[item]
            item_name = item
            for scale in scales:
                stats = scales[scale]
                scale_display[scale] = {}
                for id in stats:
                    scale_display[scale][id] = stats[id]
            scale_data = scale_display.get("Main", {})
            break
    
    if item_name == "":
        return None
    
    return scale_data, timestamp, scale_data, item_name


def item_weight_output(item_string: str, item_map: Dict, weight_data_path: str = None) -> Optional[Dict]:
    """Calculate weight output from item string."""
    from lib.decoders import ItemDecoder
    from lib.config import DATA_PATH
    if weight_data_path is None:
        weight_data_path = DATA_PATH / "mythic_weights.json"
    
    decoder = ItemDecoder()
    decoded_item = decoder.decode_item_string(item_string, item_map)
    if not decoded_item:
        return None
    
    item_name = decoded_item.name
    item_stats = decoded_item.stats
    item_rate = decoded_item.rates
    
    import json
    with open(weight_data_path, "r") as file:
        data = json.load(file)["Data"]
    
    if item_name not in data:
        return None
    
    item_IDs = {}
    for item in data:
        if item_name.lower() == item.lower():
            scales = data[item]
            item_IDs.update({item: {}})
            for scale in scales:
                stats = data[item][scale]
                rate_values = []
                weighing_factors = []
                for stat_id in stats:
                    actual_ID = item_stats.get(stat_id, 0)
                    rating = item_rate.get(stat_id, 0.0)
                    factor = float(stats[stat_id]) / 100
                    if factor < 0:
                        factor = abs(factor)
                        rating = 100 - float(rating)
                    weighing_factors.append(factor)
                    rate_values.append(float(rating))
                product = list(map(lambda x, y: x * y, rate_values, weighing_factors))
                weighted_overall = round(sum(product), 2)
                item_IDs[item][scale] = weighted_overall
    return item_IDs

