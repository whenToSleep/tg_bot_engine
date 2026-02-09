"""Utility functions for game mechanics.

This module provides reusable utilities for common game mechanics:
- Weighted random selection (loot drops, gacha pulls)
- Probability calculations
- Collection management helpers
"""

import random
from typing import List, Dict, Any, Optional, Callable, TypeVar

T = TypeVar('T')


def weighted_choice(
    items: List[Dict[str, Any]], 
    weight_key: str = "weight"
) -> Optional[Dict[str, Any]]:
    """Select item based on weights using weighted random.
    
    This is useful for loot tables, gacha pulls, or any weighted probability system.
    
    Args:
        items: List of dicts, each containing a weight value
        weight_key: Key name for the weight value (default: "weight")
        
    Returns:
        Selected item dict, or None if items list is empty
        
    Example:
        >>> loot_table = [
        ...     {"item_id": "sword", "weight": 70},
        ...     {"item_id": "gem", "weight": 30}
        ... ]
        >>> result = weighted_choice(loot_table, "weight")
        >>> print(result["item_id"])  # "sword" (70% chance) or "gem" (30%)
        
    Note:
        If all weights are 0, returns random choice with equal probability.
    """
    if not items:
        return None
    
    total_weight = sum(item.get(weight_key, 0) for item in items)
    
    # If no weights, return random choice
    if total_weight == 0:
        return random.choice(items)
    
    # Weighted selection
    roll = random.uniform(0, total_weight)
    current = 0
    
    for item in items:
        current += item.get(weight_key, 0)
        if roll <= current:
            return item
    
    return items[-1]  # Fallback to last item


def roll_loot_table(loot_table: List[Dict[str, Any]]) -> List[str]:
    """Roll for items from a loot table with independent chances.
    
    Each entry in the loot table is rolled independently. Multiple items can drop.
    
    Args:
        loot_table: List of loot entries with structure:
            {
                "item_id": str,
                "chance": float (0.0-1.0),
                "min_quantity": int (optional, default 1),
                "max_quantity": int (optional, default 1)
            }
        
    Returns:
        List of item_ids that dropped (can include duplicates)
        
    Example:
        >>> loot = [
        ...     {"item_id": "gold", "chance": 1.0, "min_quantity": 5, "max_quantity": 10},
        ...     {"item_id": "gem", "chance": 0.1, "min_quantity": 1, "max_quantity": 1}
        ... ]
        >>> dropped = roll_loot_table(loot)
        >>> print(dropped)  # ['gold', 'gold', 'gold', ...] (always 5-10 gold, sometimes gem)
    """
    dropped = []
    
    for entry in loot_table:
        # Roll for this entry
        if random.random() <= entry.get("chance", 0):
            item_id = entry["item_id"]
            min_qty = entry.get("min_quantity", 1)
            max_qty = entry.get("max_quantity", 1)
            quantity = random.randint(min_qty, max_qty)
            
            # Add items to dropped list
            dropped.extend([item_id] * quantity)
    
    return dropped


def gacha_pull(
    card_pool: List[Dict[str, Any]], 
    rarity_weights: Dict[str, float],
    rarity_key: str = "rarity"
) -> Optional[Dict[str, Any]]:
    """Perform a gacha pull with rarity-based weighted system.
    
    Two-step process:
    1. Roll for rarity based on weights
    2. Select random card from that rarity
    
    Args:
        card_pool: All available cards/items
        rarity_weights: Dict mapping rarity names to weights
            Example: {"common": 70, "rare": 25, "epic": 4, "legendary": 1}
        rarity_key: Key name for rarity field in card dicts (default: "rarity")
        
    Returns:
        Selected card/item dict, or None if pool is empty
        
    Example:
        >>> cards = [
        ...     {"id": "card1", "rarity": "common", "name": "Goblin"},
        ...     {"id": "card2", "rarity": "legendary", "name": "Dragon"}
        ... ]
        >>> weights = {"common": 99, "legendary": 1}
        >>> result = gacha_pull(cards, weights)
        >>> print(result["name"])  # Usually "Goblin", rarely "Dragon"
    """
    if not card_pool:
        return None
    
    # Step 1: Roll for rarity
    rarities = [
        {"rarity": rarity_name, "weight": weight}
        for rarity_name, weight in rarity_weights.items()
    ]
    selected_rarity_entry = weighted_choice(rarities, "weight")
    
    if not selected_rarity_entry:
        return random.choice(card_pool)
    
    selected_rarity = selected_rarity_entry["rarity"]
    
    # Step 2: Get all cards of that rarity
    cards_of_rarity = [
        card for card in card_pool 
        if card.get(rarity_key) == selected_rarity
    ]
    
    # If no cards of that rarity, return random card
    if not cards_of_rarity:
        return random.choice(card_pool)
    
    return random.choice(cards_of_rarity)


def calculate_offline_progress(
    last_login_timestamp: float,
    current_timestamp: float,
    production_rate_per_second: float,
    max_offline_hours: int = 8
) -> Dict[str, Any]:
    """Calculate resources earned during offline time.
    
    Useful for idle/clicker games where players earn resources while offline.
    
    Args:
        last_login_timestamp: Unix timestamp of last login
        current_timestamp: Unix timestamp of current login
        production_rate_per_second: Resources generated per second
        max_offline_hours: Maximum offline time to count (prevents exploits)
        
    Returns:
        Dict with keys:
            - "offline_seconds": Actual offline time (capped)
            - "uncapped_seconds": Real offline time (for display)
            - "earned": Resources earned
            - "was_capped": Boolean indicating if cap was applied
            
    Example:
        >>> last = 1609459200  # 2021-01-01 00:00:00
        >>> now = last + 10 * 3600  # 10 hours later
        >>> result = calculate_offline_progress(last, now, 10.0, max_offline_hours=8)
        >>> print(result)
        {
            "offline_seconds": 28800,  # 8 hours (capped)
            "uncapped_seconds": 36000,  # 10 hours (actual)
            "earned": 288000,  # 8 hours * 3600 * 10
            "was_capped": True
        }
    """
    offline_seconds = current_timestamp - last_login_timestamp
    max_seconds = max_offline_hours * 3600
    
    capped_seconds = min(offline_seconds, max_seconds)
    was_capped = offline_seconds > max_seconds
    
    earned = int(production_rate_per_second * capped_seconds)
    
    return {
        "offline_seconds": capped_seconds,
        "uncapped_seconds": offline_seconds,
        "earned": earned,
        "was_capped": was_capped
    }


def calculate_exponential_cost(
    base_cost: int,
    current_level: int,
    multiplier: float = 1.15
) -> int:
    """Calculate exponential cost for upgrades.
    
    Common in idle/clicker games where costs increase exponentially.
    
    Args:
        base_cost: Initial cost at level 0
        current_level: Current level (cost for NEXT level)
        multiplier: Growth factor (default 1.15 = 15% increase per level)
        
    Returns:
        Cost for next level
        
    Example:
        >>> calculate_exponential_cost(100, 0)  # First purchase
        100
        >>> calculate_exponential_cost(100, 1)  # Second purchase
        115
        >>> calculate_exponential_cost(100, 10)  # 11th purchase
        404
        
    Note:
        Formula: base_cost * (multiplier ^ current_level)
    """
    return int(base_cost * (multiplier ** current_level))


def calculate_exponential_production(
    base_production: float,
    current_level: int,
    multiplier: float = 1.07
) -> float:
    """Calculate exponential production rate.
    
    Common in idle games where production scales with building level.
    
    Args:
        base_production: Production at level 1
        current_level: Current building level
        multiplier: Growth factor (default 1.07 = 7% increase per level)
        
    Returns:
        Production rate at current level
        
    Example:
        >>> calculate_exponential_production(1.0, 1)  # Level 1
        1.0
        >>> calculate_exponential_production(1.0, 10)  # Level 10
        1.97
        >>> calculate_exponential_production(1.0, 50)  # Level 50
        29.46
        
    Note:
        Formula: base_production * (multiplier ^ (current_level - 1))
        Level 1 returns base_production without multiplier
    """
    if current_level <= 0:
        return 0.0
    
    return base_production * (multiplier ** (current_level - 1))


def merge_item_stacks(
    inventory: Dict[str, int],
    item_id: str,
    quantity: int,
    max_stack: int = 99
) -> Dict[str, Any]:
    """Add items to inventory with stack limit handling.
    
    Args:
        inventory: Current inventory dict {item_id: quantity}
        item_id: Item to add
        quantity: Quantity to add
        max_stack: Maximum stack size (default 99)
        
    Returns:
        Dict with keys:
            - "added": Quantity actually added
            - "overflow": Quantity that couldn't fit
            - "new_quantity": New quantity in inventory
            
    Example:
        >>> inv = {"potion": 95}
        >>> result = merge_item_stacks(inv, "potion", 10, max_stack=99)
        >>> print(result)
        {"added": 4, "overflow": 6, "new_quantity": 99}
        >>> print(inv)
        {"potion": 99}
    """
    current = inventory.get(item_id, 0)
    available_space = max(0, max_stack - current)
    
    added = min(quantity, available_space)
    overflow = quantity - added
    new_quantity = current + added
    
    inventory[item_id] = new_quantity
    
    return {
        "added": added,
        "overflow": overflow,
        "new_quantity": new_quantity
    }


def filter_entities(
    entities: Dict[str, Dict[str, Any]],
    filter_func: Callable[[Dict[str, Any]], bool]
) -> List[Dict[str, Any]]:
    """Filter entities based on custom predicate.
    
    Helper function for filtering game entities.
    
    Args:
        entities: Dict of entity_id -> entity_data
        filter_func: Function that takes entity and returns bool
        
    Returns:
        List of entities matching the filter
        
    Example:
        >>> entities = {
        ...     "player1": {"_type": "player", "level": 10},
        ...     "player2": {"_type": "player", "level": 5},
        ...     "mob1": {"_type": "mob"}
        ... }
        >>> high_level = filter_entities(
        ...     entities, 
        ...     lambda e: e.get("_type") == "player" and e.get("level", 0) > 7
        ... )
        >>> print(len(high_level))
        1
    """
    return [entity for entity in entities.values() if filter_func(entity)]

