"""Stat modifiers system for buffs, debuffs, and dynamic stat calculation.

This module provides a comprehensive system for modifying entity stats:
- Buffs (positive effects)
- Debuffs (negative effects)
- Equipment bonuses
- Temporary effects with duration

Example:
    >>> from engine.core.modifiers import Modifier, ModifierType, StatCalculator
    >>> 
    >>> # Create a buff: +50% attack for 3 turns
    >>> buff = Modifier("attack", ModifierType.PERCENT, 0.5, "buff_strength", duration=3)
    >>> 
    >>> # Apply to entity
    >>> entity = {"base_attack": 10, "modifiers": [buff.to_dict()]}
    >>> stats = StatCalculator.get_all_stats(entity)
    >>> print(stats["attack"])  # 15.0 (10 * 1.5)
"""

from typing import Dict, Any, List
from enum import Enum


class ModifierType(Enum):
    """Types of stat modifiers.
    
    Attributes:
        FLAT: Additive bonus (e.g., +10 attack)
        PERCENT: Percentage bonus (e.g., +20% attack = x1.2)
        MULTIPLY: Multiplicative bonus (e.g., x2 attack)
    """
    FLAT = "flat"
    PERCENT = "percent"
    MULTIPLY = "multiply"


class Modifier:
    """A stat modifier (buff, debuff, or equipment bonus).
    
    Modifiers can be temporary (with duration) or permanent (duration=-1).
    They stack additively within the same type, then multiply across types.
    
    Attributes:
        stat: Name of stat to modify (e.g., "attack", "defense", "hp")
        type: Type of modifier (FLAT, PERCENT, or MULTIPLY)
        value: Modifier value (10 for +10, 0.2 for +20%, 2.0 for x2)
        source: Source identifier (e.g., "buff_strength", "item_sword")
        duration: Turns remaining (-1 = permanent, 0 = expired, >0 = active)
    
    Example:
        >>> # +10 flat attack from sword
        >>> mod1 = Modifier("attack", ModifierType.FLAT, 10, "item_sword")
        >>> 
        >>> # +20% attack from buff
        >>> mod2 = Modifier("attack", ModifierType.PERCENT, 0.2, "buff_strength", duration=3)
        >>> 
        >>> # x2 damage from critical hit
        >>> mod3 = Modifier("attack", ModifierType.MULTIPLY, 2.0, "critical_hit", duration=1)
    """
    
    def __init__(
        self,
        stat: str,
        type: ModifierType,
        value: float,
        source: str,
        duration: int = -1
    ):
        """Initialize a modifier.
        
        Args:
            stat: Stat name to modify
            type: Modifier type (FLAT, PERCENT, MULTIPLY)
            value: Modifier value
            source: Source identifier
            duration: Turns remaining (-1 for permanent)
        """
        self.stat = stat
        self.type = type
        self.value = value
        self.source = source
        self.duration = duration
    
    def apply(self, base_value: float) -> float:
        """Apply this modifier to a base value.
        
        Args:
            base_value: Original value to modify
            
        Returns:
            Modified value
            
        Example:
            >>> mod = Modifier("attack", ModifierType.PERCENT, 0.5, "buff")
            >>> mod.apply(10)  # 15.0 (10 * 1.5)
            15.0
        """
        if self.type == ModifierType.FLAT:
            return base_value + self.value
        elif self.type == ModifierType.PERCENT:
            return base_value * (1 + self.value)
        elif self.type == ModifierType.MULTIPLY:
            return base_value * self.value
        return base_value
    
    def tick(self) -> bool:
        """Decrease duration by 1 turn.
        
        Returns:
            True if modifier is still active, False if expired
            
        Note:
            Permanent modifiers (duration=-1) always return True.
        """
        if self.duration > 0:
            self.duration -= 1
        return self.duration != 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize modifier to dictionary for storage in entity.
        
        Returns:
            Dictionary representation
            
        Example:
            >>> mod = Modifier("attack", ModifierType.FLAT, 10, "sword")
            >>> mod.to_dict()
            {'stat': 'attack', 'type': 'flat', 'value': 10, 'source': 'sword', 'duration': -1}
        """
        return {
            "stat": self.stat,
            "type": self.type.value,
            "value": self.value,
            "source": self.source,
            "duration": self.duration
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Modifier':
        """Deserialize modifier from dictionary.
        
        Args:
            data: Dictionary with modifier data
            
        Returns:
            Modifier instance
            
        Example:
            >>> data = {'stat': 'attack', 'type': 'flat', 'value': 10, 'source': 'sword'}
            >>> mod = Modifier.from_dict(data)
        """
        return Modifier(
            stat=data["stat"],
            type=ModifierType(data["type"]),
            value=data["value"],
            source=data["source"],
            duration=data.get("duration", -1)
        )


class StatCalculator:
    """Calculate final stats with modifiers applied.
    
    Handles complex stat calculations with multiple modifier sources.
    Application order: FLAT → PERCENT → MULTIPLY
    
    Example:
        >>> entity = {
        ...     "base_attack": 10,
        ...     "modifiers": [
        ...         {"stat": "attack", "type": "flat", "value": 5, "source": "sword"},
        ...         {"stat": "attack", "type": "percent", "value": 0.2, "source": "buff"}
        ...     ]
        ... }
        >>> stats = StatCalculator.get_all_stats(entity)
        >>> print(stats["attack"])  # (10 + 5) * 1.2 = 18.0
        18.0
    """
    
    @staticmethod
    def calculate_stat(
        base_value: float,
        modifiers: List[Modifier],
        stat_name: str
    ) -> float:
        """Calculate final value for a specific stat.
        
        Application order:
        1. Sum all FLAT modifiers
        2. Multiply by (1 + sum of PERCENT modifiers)
        3. Multiply by product of all MULTIPLY modifiers
        
        Args:
            base_value: Base stat value
            modifiers: List of modifiers to apply
            stat_name: Name of stat to calculate
            
        Returns:
            Final calculated value
            
        Example:
            >>> mods = [
            ...     Modifier("attack", ModifierType.FLAT, 5, "sword"),
            ...     Modifier("attack", ModifierType.PERCENT, 0.2, "buff"),
            ...     Modifier("attack", ModifierType.MULTIPLY, 2.0, "crit")
            ... ]
            >>> StatCalculator.calculate_stat(10, mods, "attack")
            36.0  # ((10 + 5) * 1.2) * 2.0
        """
        # Filter modifiers for this stat
        relevant_mods = [m for m in modifiers if m.stat == stat_name]
        
        # Step 1: Apply all FLAT bonuses (additive)
        flat_bonus = sum(
            m.value for m in relevant_mods 
            if m.type == ModifierType.FLAT
        )
        result = base_value + flat_bonus
        
        # Step 2: Apply all PERCENT bonuses (additive, then multiply)
        percent_bonus = sum(
            m.value for m in relevant_mods 
            if m.type == ModifierType.PERCENT
        )
        result = result * (1 + percent_bonus)
        
        # Step 3: Apply all MULTIPLY bonuses (multiplicative)
        for mod in [m for m in relevant_mods if m.type == ModifierType.MULTIPLY]:
            result = result * mod.value
        
        return result
    
    @staticmethod
    def get_all_stats(entity: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all final stats for an entity.
        
        Args:
            entity: Entity dictionary with base stats and modifiers
            
        Returns:
            Dictionary of stat_name -> final_value
            
        Example:
            >>> entity = {
            ...     "base_attack": 10,
            ...     "base_defense": 5,
            ...     "base_hp": 100,
            ...     "modifiers": [
            ...         {"stat": "attack", "type": "flat", "value": 5, "source": "sword"}
            ...     ]
            ... }
            >>> stats = StatCalculator.get_all_stats(entity)
            >>> stats["attack"]  # 15.0
            >>> stats["defense"]  # 5.0
            >>> stats["hp"]  # 100.0
        """
        # Define base stats with defaults
        base_stats = {
            "attack": entity.get("base_attack", entity.get("attack", 10)),
            "defense": entity.get("base_defense", entity.get("defense", 0)),
            "hp": entity.get("base_hp", entity.get("hp", 100)),
            "max_hp": entity.get("base_max_hp", entity.get("max_hp", 100)),
            "speed": entity.get("base_speed", entity.get("speed", 10)),
            "crit_chance": entity.get("base_crit_chance", entity.get("crit_chance", 0.0)),
            "crit_damage": entity.get("base_crit_damage", entity.get("crit_damage", 1.5))
        }
        
        # Load modifiers
        modifiers = [
            Modifier.from_dict(m) 
            for m in entity.get("modifiers", [])
        ]
        
        # Calculate final stats
        final_stats = {}
        for stat_name, base_value in base_stats.items():
            final_stats[stat_name] = StatCalculator.calculate_stat(
                base_value, modifiers, stat_name
            )
        
        return final_stats
    
    @staticmethod
    def update_modifier_durations(entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Update modifier durations and remove expired ones.
        
        Called at the end of each turn to tick down durations.
        
        Args:
            entity: Entity dictionary with modifiers
            
        Returns:
            List of expired modifiers (for logging/events)
            
        Example:
            >>> entity = {
            ...     "modifiers": [
            ...         {"stat": "attack", "type": "flat", "value": 5, "duration": 1},
            ...         {"stat": "defense", "type": "flat", "value": 3, "duration": 2}
            ...     ]
            ... }
            >>> expired = StatCalculator.update_modifier_durations(entity)
            >>> len(entity["modifiers"])  # 1 (attack buff expired)
            >>> len(expired)  # 1
        """
        modifiers = entity.get("modifiers", [])
        active = []
        expired = []
        
        for mod_dict in modifiers:
            mod = Modifier.from_dict(mod_dict)
            
            if mod.tick():
                # Still active
                active.append(mod.to_dict())
            else:
                # Expired
                expired.append(mod_dict)
        
        entity["modifiers"] = active
        return expired


# Convenience functions for common operations

def add_modifier(
    entity: Dict[str, Any],
    stat: str,
    type: str,
    value: float,
    source: str,
    duration: int = -1
) -> None:
    """Add a modifier to an entity.
    
    Convenience function for adding modifiers without creating Modifier objects.
    
    Args:
        entity: Entity to modify
        stat: Stat name
        type: "flat", "percent", or "multiply"
        value: Modifier value
        source: Source identifier
        duration: Turns remaining (-1 = permanent)
        
    Example:
        >>> entity = {"base_attack": 10, "modifiers": []}
        >>> add_modifier(entity, "attack", "percent", 0.2, "buff_strength", duration=3)
        >>> entity["modifiers"]
        [{'stat': 'attack', 'type': 'percent', 'value': 0.2, 'source': 'buff_strength', 'duration': 3}]
    """
    if "modifiers" not in entity:
        entity["modifiers"] = []
    
    modifier = Modifier(stat, ModifierType(type), value, source, duration)
    entity["modifiers"].append(modifier.to_dict())


def remove_modifiers_by_source(entity: Dict[str, Any], source: str) -> int:
    """Remove all modifiers from a specific source.
    
    Useful for removing equipment bonuses when unequipping, or clearing all buffs.
    
    Args:
        entity: Entity to modify
        source: Source identifier to remove
        
    Returns:
        Number of modifiers removed
        
    Example:
        >>> entity = {
        ...     "modifiers": [
        ...         {"stat": "attack", "type": "flat", "value": 5, "source": "sword"},
        ...         {"stat": "defense", "type": "flat", "value": 3, "source": "armor"}
        ...     ]
        ... }
        >>> count = remove_modifiers_by_source(entity, "sword")
        >>> count  # 1
        >>> len(entity["modifiers"])  # 1 (only armor remains)
    """
    modifiers = entity.get("modifiers", [])
    original_count = len(modifiers)
    
    entity["modifiers"] = [
        m for m in modifiers 
        if m.get("source") != source
    ]
    
    return original_count - len(entity["modifiers"])


def has_modifier_from_source(entity: Dict[str, Any], source: str) -> bool:
    """Check if entity has any modifier from a specific source.
    
    Args:
        entity: Entity to check
        source: Source identifier
        
    Returns:
        True if at least one modifier from source exists
        
    Example:
        >>> entity = {"modifiers": [{"source": "sword", "stat": "attack", ...}]}
        >>> has_modifier_from_source(entity, "sword")
        True
        >>> has_modifier_from_source(entity, "armor")
        False
    """
    return any(
        m.get("source") == source 
        for m in entity.get("modifiers", [])
    )

