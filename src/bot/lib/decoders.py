"""
Author: RawFish
Description: Item string decoding and analysis utilities
I would recommend checking out the wynntilsresolver repo for more information

I also have an API route for this, so check the docs on nori.fish
"""

from typing import Dict, Optional
from dataclasses import dataclass
from wynntilsresolver import GearItemResolver

@dataclass
class DecodedItem:
    name: str
    stats: Dict[str, int]
    rates: Dict[str, float]
    shiny: Optional[str]
    item_tier: str
    misc: Dict

class ItemDecoder:
    def decode_item_string(self, item_string: str, item_data: Dict) -> Optional[DecodedItem]:
        """Decode a Wynntils item string format"""
        try:
            item = GearItemResolver.from_utf16(item_string)
            
            stats_output = {
                item.name: {},
                "rate": {},
                "shiny": None,
                "item_tier": self._get_item_tier(item, item_data),
                "misc": {"reroll": item.rerolls if hasattr(item, "rerolls") else None}
            }

            id_range = item_data[item.name]["identifications"]
            if item.shiny:
                stats_output["shiny"] = f"{item.shiny.display_name}: {item.shiny.value}"

            for stat in item.identifications:
                if stat.roll >= 0:
                    id_rolled = self._calculate_rolled_value(stat, id_range[stat.id])
                    percentage = self._calculate_percentage(stat, id_range[stat.id], id_rolled)
                    
                    stats_output[item.name][stat.id] = id_rolled
                    stats_output["rate"][stat.id] = round(percentage, 2)

            return DecodedItem(**stats_output)

        except Exception as error:
            print(f"Decode error: {error}")
            return None

    def _calculate_rolled_value(self, stat, id_range):
        """Calculate the rolled value for a stat"""
        pass

    def _calculate_percentage(self, stat, id_range, rolled_value):
        """Calculate the percentage for a stat roll"""
        pass

    def _get_item_tier(self, item, item_data):
        """Determine item tier"""
        pass