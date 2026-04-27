"""
Author: RawFish
Description: Item string decoding and analysis utilities
I would recommend checking out the wynntilsresolver repo for more information

I also have an API route for this, so check the docs on nori.fish
"""

from typing import Dict, Optional
from dataclasses import dataclass
from wynntilsresolver import GearItemResolver

from lib.wynntils_itemdb_patch import apply_wynntils_itemdb_identification_coercion

apply_wynntils_itemdb_identification_coercion()

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
            name = item.name
            id_range = item_data.get(name, {}).get("identifications", {})

            stats: Dict[str, int] = {}
            rates: Dict[str, float] = {}
            shiny = None

            if item.shiny:
                shiny = f"{item.shiny.display_name}: {item.shiny.value}"

            for stat in item.identifications:
                if stat.roll >= 0 and stat.id in id_range:
                    stat_data = id_range[stat.id]
                    if not isinstance(stat_data, dict):
                        stats[stat.id] = stat_data
                        rates[stat.id] = 100.0
                        continue
                    id_rolled = self._calculate_rolled_value(stat, stat_data)
                    percentage = self._calculate_percentage(stat, stat_data, id_rolled)
                    stats[stat.id] = id_rolled
                    rates[stat.id] = round(percentage, 2)

            return DecodedItem(
                name=name,
                stats=stats,
                rates=rates,
                shiny=shiny,
                item_tier=self._get_item_tier(item, item_data),
                misc={"reroll": item.rerolls if hasattr(item, "rerolls") else None},
            )

        except Exception as error:
            print(f"Decode error: {error}")
            if getattr(error, "__cause__", None) is not None:
                print(f"  cause ({type(error.__cause__).__name__}): {error.__cause__}")
            return None

    def _calculate_rolled_value(self, stat, stat_data: Dict) -> int:
        id_base = stat_data.get("raw", 0)
        if stat.roll > 0:
            id_rolled = round((stat.roll / 100) * id_base, 2)
            if abs(abs(id_rolled) - abs(int(id_rolled))) == 0.5:
                id_rolled = int(id_rolled) + 1 if id_base > 0 else int(id_rolled)
            else:
                id_rolled = round(id_rolled)
        else:
            id_rolled = stat.roll
        return id_rolled

    def _calculate_percentage(self, stat, stat_data: Dict, rolled_value: int) -> float:
        id_min = stat_data.get("min", 0)
        id_max = stat_data.get("max", 0)
        if id_min == id_max:
            return 100.0
        if stat.base > 0:
            return (rolled_value - id_min) / (id_max - id_min) * 100
        else:
            return (1 - (id_max - rolled_value) / (id_max - id_min)) * 100

    def _get_item_tier(self, item, item_data: Dict) -> str:
        return item_data.get(item.name, {}).get("tier", "Unknown")