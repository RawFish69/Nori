"""
Feature engineering for item price prediction.

This module extracts comprehensive features from item data including ALL possible stats
from the game's stat system. The full list of stats is loaded from id_map.json to ensure
complete feature representation for ML models.

Feature Vector Structure:
- 120 stat values (one for each stat in id_map.json)
- 120 stat rates (roll percentages for each stat)
- 13 item type features (one-hot encoded: wand, spear, bow, dagger, relik, helmet, etc.)
- 6 tier features (one-hot encoded: mythic, fabled, legendary, rare, unique, unknown)
- 8 metadata features (level requirement, shiny, reroll count, weight, stat counts, aggregates)

Total: ~267 features per item, giving models complete understanding of item properties.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sklearn.preprocessing import LabelEncoder, StandardScaler
import json
from pathlib import Path
from lib.config import BOT_PATH


class ItemFeatureEngineer:
    """Extracts comprehensive features from item data for ML models."""
    
    def __init__(self, stat_mapping: Optional[Dict[str, str]] = None, id_map_path: Optional[Path] = None):
        self.stat_mapping = stat_mapping or {}
        self.id_map_path = id_map_path or (BOT_PATH / "id_map.json")
        self.all_stat_ids = self._load_all_stat_ids()
        self.stat_order = self._get_stat_order()
        self.item_type_encoder = LabelEncoder()
        self.tier_encoder = LabelEncoder()
        self._fitted = False
    
    def _load_all_stat_ids(self) -> List[str]:
        """Load all stat IDs from id_map.json to ensure complete feature coverage."""
        try:
            with open(self.id_map_path, "r") as f:
                id_map = json.load(f)
            # Reverse the mapping: id -> stat_name
            stat_ids = {v: k for k, v in id_map.items()}
            # Return sorted list of stat names for consistent ordering
            return sorted(id_map.keys())
        except Exception as e:
            print(f"Warning: Could not load id_map.json: {e}")
            # Fallback to a basic set if file not found
            return [
                "spellDamage", "elementalSpellDamage", "mainAttackDamage",
                "elementalMainAttackDamage", "healthRegen", "manaRegen",
                "lifeSteal", "manaSteal", "xpBonus", "lootBonus",
                "rawStrength", "rawDexterity", "rawIntelligence",
                "rawDefence", "rawAgility", "rawHealth", "rawMaxMana",
            ]
    
    def _get_stat_order(self) -> List[str]:
        """
        Get ordered list of all stats for consistent feature vectors.
        
        Returns all 120 stats from id_map.json in sorted order to ensure
        consistent feature vector dimensions across all items.
        """
        return self.all_stat_ids
    
    def get_feature_vector_size(self) -> int:
        """
        Get the expected size of the feature vector.
        
        Returns:
            Total number of features: 
            - 2 * len(stat_order) (stat values + stat rates for all stats)
            - 13 (item type one-hot)
            - 6 (tier one-hot)
            - 8 (metadata: level, shiny, reroll, weight, stat counts, aggregates)
        """
        return (2 * len(self.stat_order)) + 13 + 6 + 8
    
    def extract_features_from_item_data(
        self,
        item_data: Dict[str, Any],
        weight: Optional[float] = None,
        item_name: Optional[str] = None
    ) -> np.ndarray:
        """
        Extract comprehensive feature vector from item data.
        
        Includes ALL stats from id_map.json to give models full understanding of item properties.
        Features include:
        - All stat values (raw and percentage-based)
        - All stat roll percentages (rates)
        - Item type (one-hot encoded)
        - Tier/rarity (one-hot encoded)
        - Level requirement (normalized)
        - Shiny status
        - Reroll count
        - Weight (if available)
        - Derived features (stat count, high-value stat count)
        """
        features = []
        
        # Extract stats dict - could be under item name key or directly in item_data
        if item_data and len(item_data) > 0:
            # Try to find the stats dict (usually under item name key)
            stats = {}
            for key in item_data.keys():
                if key not in ["rate", "shiny", "item_type", "item_tier", "level_requirement", "misc"]:
                    if isinstance(item_data[key], dict):
                        stats = item_data[key]
                        break
            # If no nested dict found, use item_data itself (minus metadata keys)
            if not stats:
                stats = {k: v for k, v in item_data.items() 
                        if k not in ["rate", "shiny", "item_type", "item_tier", "level_requirement", "misc"]}
        else:
            stats = {}
        
        rates = item_data.get("rate", {})
        
        # Extract ALL stats in consistent order
        stat_values = []
        stat_rates = []
        
        # First, extract all known stats from stat_order (from id_map.json)
        for stat_id in self.stat_order:
            stat_value = stats.get(stat_id, 0)
            stat_values.append(float(stat_value))
            
            stat_rate = rates.get(stat_id, 0.0)
            stat_rates.append(float(stat_rate))
        
        # All stats from id_map.json are now included in stat_order
        # This ensures consistent feature vector size
        features.extend(stat_values)
        features.extend(stat_rates)
        
        item_type = item_data.get("item_type", "unknown")
        item_type_encoded = self._encode_item_type(item_type)
        features.extend(item_type_encoded)
        
        tier = item_data.get("item_tier", "unknown")
        tier_encoded = self._encode_tier(tier)
        features.extend(tier_encoded)
        
        level_req = item_data.get("level_requirement", 0)
        features.append(float(level_req) / 130.0)
        
        shiny = item_data.get("shiny")
        features.append(1.0 if shiny else 0.0)
        
        reroll = item_data.get("misc", {}).get("reroll", 0) if isinstance(item_data.get("misc"), dict) else 0
        features.append(float(reroll) / 10.0)
        
        if weight is not None:
            features.append(float(weight) / 100.0)
        else:
            avg_rate = np.mean(list(rates.values())) if rates else 0.0
            features.append(avg_rate / 100.0)
        
        # Derived features
        stat_count = len([v for v in stat_values if v != 0])
        high_value_stat_count = len([r for r in stat_rates if r > 80.0])
        very_high_value_stat_count = len([r for r in stat_rates if r > 90.0])
        
        # Normalize counts
        features.append(float(stat_count) / len(self.stat_order))  # Normalize by total possible stats
        features.append(float(high_value_stat_count) / len(self.stat_order))
        features.append(float(very_high_value_stat_count) / len(self.stat_order))
        
        # Aggregate stats by category for additional insights
        raw_stats_sum = sum([stat_values[i] for i, stat_id in enumerate(self.stat_order) if stat_id.startswith("raw")])
        elemental_stats_sum = sum([stat_values[i] for i, stat_id in enumerate(self.stat_order) if "elemental" in stat_id.lower()])
        damage_stats_sum = sum([stat_values[i] for i, stat_id in enumerate(self.stat_order) if "damage" in stat_id.lower()])
        defence_stats_sum = sum([stat_values[i] for i, stat_id in enumerate(self.stat_order) if "defence" in stat_id.lower() or "defense" in stat_id.lower()])
        
        # Normalize aggregates (rough normalization)
        features.append(float(raw_stats_sum) / 1000.0)
        features.append(float(elemental_stats_sum) / 1000.0)
        features.append(float(damage_stats_sum) / 1000.0)
        features.append(float(defence_stats_sum) / 1000.0)
        
        return np.array(features, dtype=np.float32)
    
    def _encode_item_type(self, item_type: str) -> List[float]:
        """One-hot encode item type."""
        types = ["wand", "spear", "bow", "dagger", "relik", 
                "helmet", "chestplate", "leggings", "boots",
                "ring", "bracelet", "necklace", "unknown"]
        
        encoding = [0.0] * len(types)
        try:
            idx = types.index(item_type.lower())
            encoding[idx] = 1.0
        except ValueError:
            encoding[-1] = 1.0
        
        return encoding
    
    def _encode_tier(self, tier: str) -> List[float]:
        """One-hot encode tier/rarity."""
        tiers = ["mythic", "fabled", "legendary", "rare", "unique", "unknown"]
        
        encoding = [0.0] * len(tiers)
        try:
            idx = tiers.index(tier.lower())
            encoding[idx] = 1.0
        except ValueError:
            encoding[-1] = 1.0
        
        return encoding
    
    def extract_features_batch(
        self,
        items_data: List[Dict[str, Any]],
        weights: Optional[List[float]] = None
    ) -> np.ndarray:
        """Extract features for multiple items."""
        if weights is None:
            weights = [None] * len(items_data)
        
        features_list = []
        for item_data, weight in zip(items_data, weights):
            features = self.extract_features_from_item_data(item_data, weight)
            features_list.append(features)
        
        return np.array(features_list)
    
    def get_feature_names(self) -> List[str]:
        """Get feature names for interpretability."""
        names = []
        
        # All stat values (from id_map.json - all 120 stats)
        names.extend([f"stat_value_{stat}" for stat in self.stat_order])
        # All stat rates (from id_map.json - all 120 stats)
        names.extend([f"stat_rate_{stat}" for stat in self.stat_order])
        # Item type (one-hot)
        names.extend([f"item_type_{t}" for t in ["wand", "spear", "bow", "dagger", "relik",
                                                  "helmet", "chestplate", "leggings", "boots",
                                                  "ring", "bracelet", "necklace", "unknown"]])
        # Tier (one-hot)
        names.extend([f"tier_{t}" for t in ["mythic", "fabled", "legendary", "rare", "unique", "unknown"]])
        # Metadata
        names.extend([
            "level_requirement",
            "shiny",
            "reroll_count",
            "weight",
            "stat_count",
            "high_value_stat_count",
            "very_high_value_stat_count",
            "raw_stats_sum",
            "elemental_stats_sum",
            "damage_stats_sum",
            "defence_stats_sum"
        ])
        
        return names


def create_item_feature_vector(
    decoded_item: Dict[str, Any],
    weight: Optional[float] = None,
    item_metadata: Optional[Dict[str, Any]] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Create feature vector from decoded item data."""
    engineer = ItemFeatureEngineer()
    
    item_data = decoded_item.copy()
    if item_metadata:
        item_data.update(item_metadata)
    
    if "item_type" not in item_data and item_metadata:
        item_data["item_type"] = item_metadata.get("item_type", "unknown")
    
    features = engineer.extract_features_from_item_data(item_data, weight)
    
    return features, {
        "feature_names": engineer.get_feature_names(),
        "n_features": len(features)
    }
