"""Bonus calculation system for idle games with multipliers from multiple sources.

This module provides a flexible system for calculating bonuses from:
- Achievements (+5% production)
- Items/Equipment (+10% production)
- Upgrades (+20% production)
- Caps (max offline time, max storage)

Example:
    >>> from engine.core.bonuses import BonusCalculator
    >>> 
    >>> calc = BonusCalculator()
    >>> calc.add_bonus("production", "percent", 0.05, "achievement_novice")
    >>> calc.add_bonus("production", "percent", 0.10, "item_hammer")
    >>> 
    >>> base_production = 10
    >>> final = calc.calculate("production", base_production)
    >>> print(final)  # 11.5 (10 * 1.15)
"""

from typing import Dict, Any, List, Optional


class BonusCalculator:
    """Calculate bonuses from multiple sources with caps.
    
    Handles additive and multiplicative bonuses from various sources,
    with optional caps (limits) on final values.
    
    Example:
        >>> calc = BonusCalculator()
        >>> calc.add_bonus("gold", "percent", 0.2, "achievement_rich")
        >>> calc.add_bonus("gold", "flat", 100, "item_coin_purse")
        >>> calc.add_cap("gold", 10000)
        >>> 
        >>> base_gold = 1000
        >>> final = calc.calculate("gold", base_gold)  # min(1300, 10000) = 1300
    """
    
    def __init__(self):
        """Initialize bonus calculator with empty bonuses and caps."""
        self.bonuses: Dict[str, List[Dict[str, Any]]] = {}
        self.caps: Dict[str, float] = {}
    
    def add_bonus(
        self,
        category: str,
        type: str,
        value: float,
        source: str
    ) -> None:
        """Add a bonus to a category.
        
        Args:
            category: Bonus category (e.g., "production", "gold", "offline_time")
            type: "flat" for additive, "percent" for percentage, "multiply" for multiplicative
            value: Bonus value (5 for +5, 0.2 for +20%, 2.0 for x2)
            source: Source identifier (e.g., "achievement_1", "item_hammer")
            
        Example:
            >>> calc = BonusCalculator()
            >>> calc.add_bonus("production", "percent", 0.15, "upgrade_efficiency")
            >>> calc.add_bonus("production", "flat", 10, "item_tool")
        """
        if category not in self.bonuses:
            self.bonuses[category] = []
        
        self.bonuses[category].append({
            "type": type,
            "value": value,
            "source": source
        })
    
    def remove_bonus(self, category: str, source: str) -> int:
        """Remove all bonuses from a specific source.
        
        Args:
            category: Bonus category
            source: Source identifier to remove
            
        Returns:
            Number of bonuses removed
            
        Example:
            >>> calc = BonusCalculator()
            >>> calc.add_bonus("gold", "percent", 0.1, "item_ring")
            >>> calc.remove_bonus("gold", "item_ring")
            1
        """
        if category not in self.bonuses:
            return 0
        
        original_count = len(self.bonuses[category])
        self.bonuses[category] = [
            b for b in self.bonuses[category]
            if b["source"] != source
        ]
        
        return original_count - len(self.bonuses[category])
    
    def add_cap(self, category: str, cap_value: float) -> None:
        """Set a cap (maximum limit) for a category.
        
        Args:
            category: Category to cap
            cap_value: Maximum allowed value
            
        Example:
            >>> calc = BonusCalculator()
            >>> calc.add_cap("offline_hours", 8)
            >>> calc.calculate("offline_hours", 24)  # Returns 8 (capped)
            8.0
        """
        self.caps[category] = cap_value
    
    def get_cap(self, category: str) -> Optional[float]:
        """Get the cap value for a category.
        
        Args:
            category: Category to check
            
        Returns:
            Cap value or None if no cap
        """
        return self.caps.get(category)
    
    def calculate(
        self,
        category: str,
        base_value: float,
        apply_cap: bool = True
    ) -> float:
        """Calculate final value with all bonuses applied.
        
        Application order:
        1. Sum all FLAT bonuses
        2. Multiply by (1 + sum of PERCENT bonuses)
        3. Multiply by product of all MULTIPLY bonuses
        4. Apply cap if enabled
        
        Args:
            category: Category to calculate
            base_value: Base value before bonuses
            apply_cap: Whether to apply cap limit
            
        Returns:
            Final calculated value
            
        Example:
            >>> calc = BonusCalculator()
            >>> calc.add_bonus("gold", "flat", 100, "item")
            >>> calc.add_bonus("gold", "percent", 0.5, "achievement")
            >>> calc.add_cap("gold", 500)
            >>> calc.calculate("gold", 200)  # (200 + 100) * 1.5 = 450, capped to 500
            450.0
        """
        bonuses = self.bonuses.get(category, [])
        
        # Step 1: Apply FLAT bonuses (additive)
        flat_bonus = sum(
            b["value"] for b in bonuses
            if b["type"] == "flat"
        )
        result = base_value + flat_bonus
        
        # Step 2: Apply PERCENT bonuses (additive, then multiply)
        percent_bonus = sum(
            b["value"] for b in bonuses
            if b["type"] == "percent"
        )
        result = result * (1 + percent_bonus)
        
        # Step 3: Apply MULTIPLY bonuses (multiplicative)
        for bonus in [b for b in bonuses if b["type"] == "multiply"]:
            result = result * bonus["value"]
        
        # Step 4: Apply cap if enabled
        if apply_cap and category in self.caps:
            result = min(result, self.caps[category])
        
        return result
    
    def get_all_bonuses(self, category: str) -> List[Dict[str, Any]]:
        """Get all bonuses for a category.
        
        Args:
            category: Category to query
            
        Returns:
            List of bonus dictionaries
            
        Example:
            >>> calc = BonusCalculator()
            >>> calc.add_bonus("gold", "percent", 0.1, "ach1")
            >>> calc.get_all_bonuses("gold")
            [{'type': 'percent', 'value': 0.1, 'source': 'ach1'}]
        """
        return self.bonuses.get(category, [])
    
    def has_bonus_from_source(self, category: str, source: str) -> bool:
        """Check if a bonus from a specific source exists.
        
        Args:
            category: Category to check
            source: Source identifier
            
        Returns:
            True if bonus exists
            
        Example:
            >>> calc = BonusCalculator()
            >>> calc.add_bonus("gold", "flat", 10, "item_1")
            >>> calc.has_bonus_from_source("gold", "item_1")
            True
        """
        return any(
            b["source"] == source
            for b in self.bonuses.get(category, [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage.
        
        Returns:
            Dictionary representation
            
        Example:
            >>> calc = BonusCalculator()
            >>> calc.add_bonus("gold", "percent", 0.1, "ach")
            >>> calc.add_cap("gold", 1000)
            >>> data = calc.to_dict()
        """
        return {
            "bonuses": self.bonuses,
            "caps": self.caps
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'BonusCalculator':
        """Deserialize from dictionary.
        
        Args:
            data: Dictionary with bonuses and caps
            
        Returns:
            BonusCalculator instance
            
        Example:
            >>> data = {"bonuses": {"gold": [...]}, "caps": {"gold": 1000}}
            >>> calc = BonusCalculator.from_dict(data)
        """
        calc = BonusCalculator()
        calc.bonuses = data.get("bonuses", {})
        calc.caps = data.get("caps", {})
        return calc


def calculate_bonus_summary(calc: BonusCalculator, category: str) -> Dict[str, Any]:
    """Generate a summary of bonuses for display to player.
    
    Args:
        calc: BonusCalculator instance
        category: Category to summarize
        
    Returns:
        Dictionary with flat_total, percent_total, multiply_total, cap
        
    Example:
        >>> calc = BonusCalculator()
        >>> calc.add_bonus("gold", "flat", 10, "item_1")
        >>> calc.add_bonus("gold", "percent", 0.2, "ach_1")
        >>> calc.add_bonus("gold", "percent", 0.1, "ach_2")
        >>> summary = calculate_bonus_summary(calc, "gold")
        >>> summary["flat_total"]  # 10
        >>> summary["percent_total"]  # 0.3 (30%)
    """
    bonuses = calc.get_all_bonuses(category)
    
    flat_total = sum(b["value"] for b in bonuses if b["type"] == "flat")
    percent_total = sum(b["value"] for b in bonuses if b["type"] == "percent")
    multiply_total = 1.0
    for bonus in [b for b in bonuses if b["type"] == "multiply"]:
        multiply_total *= bonus["value"]
    
    return {
        "flat_total": flat_total,
        "percent_total": percent_total,
        "multiply_total": multiply_total,
        "cap": calc.get_cap(category),
        "sources": [b["source"] for b in bonuses]
    }


def load_bonuses_from_entity(entity: Dict[str, Any]) -> BonusCalculator:
    """Load bonuses from an entity (e.g., player with achievements/items).
    
    Convenience function to build a BonusCalculator from entity data.
    
    Args:
        entity: Entity with "bonuses" field
        
    Returns:
        BonusCalculator instance
        
    Example:
        >>> player = {
        ...     "bonuses": {
        ...         "bonuses": {"gold": [{"type": "percent", "value": 0.1, "source": "ach"}]},
        ...         "caps": {"gold": 10000}
        ...     }
        ... }
        >>> calc = load_bonuses_from_entity(player)
    """
    if "bonuses" in entity:
        return BonusCalculator.from_dict(entity["bonuses"])
    return BonusCalculator()


def save_bonuses_to_entity(entity: Dict[str, Any], calc: BonusCalculator) -> None:
    """Save bonuses to an entity.
    
    Args:
        entity: Entity to save to
        calc: BonusCalculator to serialize
        
    Example:
        >>> player = {}
        >>> calc = BonusCalculator()
        >>> calc.add_bonus("gold", "percent", 0.1, "ach")
        >>> save_bonuses_to_entity(player, calc)
        >>> "bonuses" in player
        True
    """
    entity["bonuses"] = calc.to_dict()

