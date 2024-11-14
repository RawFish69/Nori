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
            with open(self.weight_data_path, "r") as file:
                return json.load(file)
        except Exception as error:
            print(f"Error loading weight data: {error}")
            return {}

    def calculate_mythic_weight(self, target: str, user_inputs: List[float]) -> Optional[WeightResult]:
        """Calculate mythic item weights based on user inputs"""
        data = self.weight_data.get("Data", {})
        item_weights = []
        result = {}
        product_main = []

        # Find matching item
        for item in data:
            if target.lower() == item.lower():
                scales = data[item]
                result = {item: {}}
                
                # Calculate weights for each scale
                for scale in scales:
                    stats = scales[scale]
                    item_weights.clear()
                    
                    # Calculate individual stat weights
                    for stat_id in stats:
                        weight = float(stats[stat_id]) / 100
                        item_weights.append(weight)
                    
                    # Calculate weighted product
                    product = [x * y for x, y in zip(user_inputs, item_weights)]
                    if scale == "Main":
                        product_main = product
                    
                    weighted_overall = round(sum(product), 2)
                    result[item].update({scale: weighted_overall})

                return WeightResult(
                    item_name=item,
                    scale_weights=result[item],
                    main_products=product_main,
                    timestamp=self.weight_data.get("latest", {}).get("Timestamp", ""),
                    scale_data=scales["Main"]
                )
        
        return None

    def get_scale_info(self, target: str) -> Optional[Tuple[Dict, str, Dict, str]]:
        """Get detailed scale information for an item"""
        data = self.weight_data.get("Data", {})
        timestamp = self.weight_data.get("latest", {}).get("Timestamp", "")
        
        scale_display = {}
        index = 1
        
        for item in data:
            if target.lower() == item.lower():
                scales = data[item]
                scale_display = {item: {}}
                scale_data = scales["Main"]
                
                # Generate display content for each scale
                for scale in scales:
                    scale_content = ""
                    scale_display[item][scale] = ""
                    item_scales = scales[scale]
                    
                    for item_id in item_scales:
                        scale_content += f"{index}. {item_id}: {item_scales[item_id]}%\n"
                        index += 1
                    
                    scale_display[item][scale] = scale_content
                    index = 1
                
                return scale_display, timestamp, scale_data, item

        return None