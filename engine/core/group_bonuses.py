"""Group Bonus System - Synergy calculator for entity groups.

This module provides mechanics for calculating bonuses based on groups of entities:
- Element synergies (e.g., 3+ Fire cards = +15% ATK)
- Class synergies (e.g., 4+ Warriors = +20% DEF)
- Rarity synergies (e.g., All S-rank = +25% stats)

Designed for CCG deck building and team composition mechanics.

Example:
    >>> from engine.core.group_bonuses import GroupBonusCalculator
    >>> 
    >>> # Define synergy rules
    >>> rules = [
    ...     {
    ...         "id": "fire_synergy",
    ...         "name": "Fire Resonance",
    ...         "description": "+15% ATK for 3+ Fire cards",
    ...         "condition": {"element": "fire", "min_count": 3},
    ...         "bonus": {"stat": "atk", "type": "percent", "value": 15}
    ...     }
    ... ]
    >>> 
    >>> calculator = GroupBonusCalculator(rules)
    >>> 
    >>> deck = [
    ...     {"element": "fire", "atk": 100},
    ...     {"element": "fire", "atk": 80},
    ...     {"element": "fire", "atk": 120}
    ... ]
    >>> 
    >>> synergies = calculator.calculate(deck)
    >>> print(synergies["fire_synergy"]["active"])  # True
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class SynergyRule:
    """Defines a synergy activation rule.
    
    Attributes:
        synergy_id: Unique identifier
        name: Display name
        description: User-friendly description
        condition: Condition for activation (field: value, min_count)
        bonuses: List of bonuses to apply when active
        priority: Higher priority bonuses are applied first (default: 0)
    """
    synergy_id: str
    name: str
    description: str
    condition: Dict[str, Any]
    bonuses: List[Dict[str, Any]]
    priority: int = 0


class GroupBonusCalculator:
    """Calculates bonuses based on groups of entities.
    
    This calculator analyzes a group of entities (e.g., a deck of cards)
    and determines which synergy bonuses are active.
    
    Features:
    - Element/type-based synergies
    - Count-based thresholds
    - Custom condition functions
    - Multiple bonus types (flat, percent, multiply)
    
    Example:
        >>> rules = [
        ...     SynergyRule(
        ...         synergy_id="fire_atk",
        ...         name="Fire Synergy",
        ...         description="+15% ATK",
        ...         condition={"element": "fire", "min_count": 3},
        ...         bonuses=[{"stat": "atk", "type": "percent", "value": 15}]
        ...     )
        ... ]
        >>> 
        >>> calculator = GroupBonusCalculator(rules)
        >>> deck = [
        ...     {"element": "fire"},
        ...     {"element": "fire"},
        ...     {"element": "fire"}
        ... ]
        >>> 
        >>> result = calculator.calculate(deck)
        >>> print(result["fire_atk"]["active"])  # True
    """
    
    def __init__(self, rules: Optional[List[SynergyRule | Dict[str, Any]]] = None):
        """Initialize calculator with synergy rules.
        
        Args:
            rules: List of SynergyRule objects or dicts
        """
        self.rules: List[SynergyRule] = []
        
        if rules:
            for rule in rules:
                if isinstance(rule, dict):
                    self.add_rule_from_dict(rule)
                else:
                    self.rules.append(rule)
        
        # Sort rules by priority (higher first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def add_rule_from_dict(self, rule_dict: Dict[str, Any]) -> None:
        """Add a synergy rule from dictionary.
        
        Args:
            rule_dict: Dictionary with rule definition
        """
        rule = SynergyRule(
            synergy_id=rule_dict["id"],
            name=rule_dict.get("name", rule_dict["id"]),
            description=rule_dict.get("description", ""),
            condition=rule_dict["condition"],
            bonuses=rule_dict.get("bonus", []) if isinstance(rule_dict.get("bonus"), list) else [rule_dict["bonus"]],
            priority=rule_dict.get("priority", 0)
        )
        self.rules.append(rule)
    
    def calculate(
        self,
        entities: List[Dict[str, Any]],
        group_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate active synergies for a group of entities.
        
        Args:
            entities: List of entities (e.g., cards in deck)
            group_context: Optional context data
            
        Returns:
            Dictionary mapping synergy_id to synergy state:
            {
                "synergy_id": {
                    "active": bool,
                    "name": str,
                    "description": str,
                    "bonuses": list,
                    "matching_count": int
                }
            }
        """
        results = {}
        
        for rule in self.rules:
            matching_entities = self._count_matching(entities, rule.condition)
            min_count = rule.condition.get("min_count", 1)
            active = matching_entities >= min_count
            
            results[rule.synergy_id] = {
                "active": active,
                "name": rule.name,
                "description": rule.description,
                "bonuses": rule.bonuses if active else [],
                "matching_count": matching_entities,
                "required_count": min_count
            }
        
        return results
    
    def _count_matching(
        self,
        entities: List[Dict[str, Any]],
        condition: Dict[str, Any]
    ) -> int:
        """Count entities matching condition.
        
        Args:
            entities: List of entities
            condition: Condition dict (field: value, min_count)
            
        Returns:
            Number of matching entities
        """
        count = 0
        
        # Extract condition parameters
        min_count = condition.get("min_count", 1)
        condition_copy = {k: v for k, v in condition.items() if k != "min_count"}
        
        if not condition_copy:
            # No specific conditions, just count all
            return len(entities)
        
        # Count entities matching all conditions
        for entity in entities:
            matches = all(
                entity.get(field) == value
                for field, value in condition_copy.items()
            )
            if matches:
                count += 1
        
        return count
    
    def get_active_bonuses(
        self,
        entities: List[Dict[str, Any]],
        group_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get all active synergy bonuses for entities.
        
        Args:
            entities: List of entities
            group_context: Optional context
            
        Returns:
            List of active bonus dicts
        """
        synergies = self.calculate(entities, group_context)
        
        all_bonuses = []
        for synergy_data in synergies.values():
            if synergy_data["active"]:
                all_bonuses.extend(synergy_data["bonuses"])
        
        return all_bonuses
    
    def apply_to_entity(
        self,
        entities: List[Dict[str, Any]],
        target_entity: Dict[str, Any]
    ) -> None:
        """Apply synergy bonuses to an entity as modifiers.
        
        Args:
            entities: List of entities (e.g., deck cards)
            target_entity: Entity to apply bonuses to (e.g., player)
        """
        from engine.core.modifiers import add_modifier
        
        synergies = self.calculate(entities)
        
        for synergy_id, synergy_data in synergies.items():
            if synergy_data["active"]:
                for bonus in synergy_data["bonuses"]:
                    # Convert bonus to modifier
                    stat_name = bonus.get("stat", "unknown")
                    value = bonus.get("value", 0)
                    bonus_type = bonus.get("type", "flat")
                    
                    # For percent bonuses, StatCalculator expects decimal (e.g., 0.15 not 15)
                    if bonus_type == "percent":
                        value = value / 100.0
                    
                    # Add modifier to entity
                    add_modifier(
                        target_entity,
                        stat=stat_name,
                        type=bonus_type,
                        value=value,
                        source=f"synergy:{synergy_id}",
                        duration=-1  # Synergies are permanent while active
                    )


def create_element_synergy_rule(
    element: str,
    min_count: int,
    bonus_stat: str,
    bonus_value: float,
    bonus_type: str = "percent"
) -> SynergyRule:
    """Factory function to create element synergy rule.
    
    Args:
        element: Element type (e.g., "fire", "water")
        min_count: Minimum cards needed
        bonus_stat: Stat to boost (e.g., "atk", "def")
        bonus_value: Bonus value
        bonus_type: Type of bonus (flat/percent/multiply)
        
    Returns:
        SynergyRule
        
    Example:
        >>> rule = create_element_synergy_rule(
        ...     element="fire",
        ...     min_count=3,
        ...     bonus_stat="atk",
        ...     bonus_value=15,
        ...     bonus_type="percent"
        ... )
    """
    synergy_id = f"{element}_synergy_{min_count}"
    name = f"{element.title()} Resonance"
    description = f"+{bonus_value}{'%' if bonus_type == 'percent' else ''} {bonus_stat.upper()} with {min_count}+ {element.title()} cards"
    
    return SynergyRule(
        synergy_id=synergy_id,
        name=name,
        description=description,
        condition={"element": element, "min_count": min_count},
        bonuses=[{
            "stat": bonus_stat,
            "type": bonus_type,
            "value": bonus_value
        }]
    )


def create_rarity_synergy_rule(
    rarity: str,
    min_count: int,
    bonus_stats: List[str],
    bonus_value: float,
    bonus_type: str = "percent"
) -> SynergyRule:
    """Factory function to create rarity synergy rule.
    
    Args:
        rarity: Rarity tier (e.g., "S", "SS")
        min_count: Minimum cards needed
        bonus_stats: List of stats to boost
        bonus_value: Bonus value
        bonus_type: Type of bonus
        
    Returns:
        SynergyRule
        
    Example:
        >>> rule = create_rarity_synergy_rule(
        ...     rarity="S",
        ...     min_count=3,
        ...     bonus_stats=["atk", "def"],
        ...     bonus_value=10,
        ...     bonus_type="percent"
        ... )
    """
    synergy_id = f"rarity_{rarity}_{min_count}"
    name = f"{rarity}-Rank Assembly"
    description = f"+{bonus_value}{'%' if bonus_type == 'percent' else ''} to all stats with {min_count}+ {rarity}-rank cards"
    
    bonuses = [
        {"stat": stat, "type": bonus_type, "value": bonus_value}
        for stat in bonus_stats
    ]
    
    return SynergyRule(
        synergy_id=synergy_id,
        name=name,
        description=description,
        condition={"rarity": rarity, "min_count": min_count},
        bonuses=bonuses
    )


def analyze_deck_composition(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze composition of a deck/group.
    
    Provides statistics about element distribution, rarity distribution, etc.
    
    Args:
        entities: List of entities
        
    Returns:
        Dictionary with composition statistics
        
    Example:
        >>> deck = [
        ...     {"element": "fire", "rarity": "C"},
        ...     {"element": "fire", "rarity": "S"},
        ...     {"element": "water", "rarity": "B"}
        ... ]
        >>> stats = analyze_deck_composition(deck)
        >>> print(stats["elements"])  # {"fire": 2, "water": 1}
    """
    elements = Counter(e.get("element") for e in entities if e.get("element"))
    rarities = Counter(e.get("rarity") for e in entities if e.get("rarity"))
    types = Counter(e.get("_type") for e in entities if e.get("_type"))
    
    return {
        "total_count": len(entities),
        "elements": dict(elements),
        "rarities": dict(rarities),
        "types": dict(types),
        "most_common_element": elements.most_common(1)[0] if elements else None,
        "most_common_rarity": rarities.most_common(1)[0] if rarities else None
    }

