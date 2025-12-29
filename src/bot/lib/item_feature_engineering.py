"""
Feature engineering for item price prediction.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sklearn.preprocessing import LabelEncoder, StandardScaler
import json


class ItemFeatureEngineer:
    """Extracts features from item data for ML models."""
    
    def __init__(self, stat_mapping: Optional[Dict[str, str]] = None):
        self.stat_mapping = stat_mapping or {}
        self.stat_order = self._get_stat_order()
        self.item_type_encoder = LabelEncoder()
        self.tier_encoder = LabelEncoder()
        self._fitted = False
    
    def _get_stat_order(self) -> List[str]:
        """Standard stat order for consistent feature vectors."""
        return [
            "spellDamage", "elementalSpellDamage", "mainAttackDamage",
            "elementalMainAttackDamage", "healthRegen", "manaRegen",
            "lifeSteal", "manaSteal", "xpBonus", "lootBonus",
            "rawStrength", "rawDexterity", "rawIntelligence",
            "rawDefence", "rawAgility", "rawHealth", "rawMaxMana",
        ]
    
    def extract_features_from_item_data(
        self,
        item_data: Dict[str, Any],
        weight: Optional[float] = None,
        item_name: Optional[str] = None
    ) -> np.ndarray:
        """Extract feature vector from item data."""
        features = []
        
        stats = item_data.get(list(item_data.keys())[0], {}) if item_data else {}
        rates = item_data.get("rate", {})
        
        stat_values = []
        stat_rates = []
        
        for stat_id in self.stat_order:
            stat_value = stats.get(stat_id, 0)
            stat_values.append(float(stat_value))
            
            stat_rate = rates.get(stat_id, 0.0)
            stat_rates.append(float(stat_rate))
        
        for stat_id, value in stats.items():
            if stat_id not in self.stat_order and stat_id != "rate":
                stat_values.append(float(value))
                stat_rates.append(float(rates.get(stat_id, 0.0)))
        
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
        
        stat_count = len([v for v in stat_values if v != 0])
        high_value_stat_count = len([r for r in stat_rates if r > 80.0])
        features.append(float(stat_count) / 10.0)
        features.append(float(high_value_stat_count) / 5.0)
        
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
        
        names.extend([f"stat_value_{stat}" for stat in self.stat_order])
        names.extend([f"stat_rate_{stat}" for stat in self.stat_order])
        names.extend([f"item_type_{t}" for t in ["wand", "spear", "bow", "dagger", "relik",
                                                  "helmet", "chestplate", "leggings", "boots",
                                                  "ring", "bracelet", "necklace", "unknown"]])
        names.extend([f"tier_{t}" for t in ["mythic", "fabled", "legendary", "rare", "unique", "unknown"]])
        names.extend([
            "level_requirement",
            "shiny",
            "reroll_count",
            "weight",
            "stat_count",
            "high_value_stat_count"
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
