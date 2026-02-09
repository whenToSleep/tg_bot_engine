"""Unique Entity System - Generate and manage unique entity instances.

This module provides utilities for creating unique instances of entities
from templates/prototypes, essential for:
- CCG/Gacha games (each card is a unique instance)
- Inventory systems (same item type, different stats)
- Equipment systems (multiple copies of same sword)

Example:
    >>> from engine.core.unique_entity import create_unique_entity
    >>> 
    >>> card_template = {
    ...     "proto_id": "dragon_card",
    ...     "name": "Ancient Dragon",
    ...     "rarity": "legendary",
    ...     "base_attack": 100
    ... }
    >>> 
    >>> # Create unique instance
    >>> card_instance = create_unique_entity(card_template, "card", owner_id="player_1")
    >>> print(card_instance["_id"])  # 'card_a1b2c3d4'
    >>> print(card_instance["proto_id"])  # 'dragon_card'
"""

import uuid
from typing import Dict, Any, Optional
from copy import deepcopy


def generate_unique_id(prefix: str = "") -> str:
    """Generate a unique ID for an entity.
    
    Args:
        prefix: Optional prefix for the ID (e.g., "card", "item")
        
    Returns:
        Unique ID string
        
    Example:
        >>> uid = generate_unique_id("card")
        >>> uid.startswith("card_")
        True
        >>> len(uid)  # "card_" + 8 chars = 13
        13
    """
    unique_part = uuid.uuid4().hex[:8]
    if prefix:
        return f"{prefix}_{unique_part}"
    return unique_part


def create_unique_entity(
    template: Dict[str, Any],
    entity_type: str,
    owner_id: Optional[str] = None,
    custom_fields: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a unique entity instance from a template.
    
    This function:
    1. Deep copies the template
    2. Generates a unique _id
    3. Preserves proto_id (template reference)
    4. Sets _type
    5. Adds owner_id if provided
    6. Merges custom_fields
    7. Sets status to "active" by default
    
    Args:
        template: Template/prototype entity
        entity_type: Type of entity (e.g., "card", "item")
        owner_id: Optional owner ID (e.g., player ID)
        custom_fields: Optional fields to override/add
        
    Returns:
        Unique entity instance
        
    Example:
        >>> template = {
        ...     "proto_id": "fire_sword",
        ...     "name": "Fire Sword",
        ...     "attack": 50
        ... }
        >>> instance = create_unique_entity(
        ...     template, 
        ...     "item",
        ...     owner_id="player_1",
        ...     custom_fields={"level": 5}
        ... )
        >>> instance["_id"]  # 'item_a1b2c3d4'
        >>> instance["proto_id"]  # 'fire_sword'
        >>> instance["owner_id"]  # 'player_1'
        >>> instance["level"]  # 5
    """
    # Deep copy to avoid modifying template
    instance = deepcopy(template)
    
    # Generate unique ID
    instance["_id"] = generate_unique_id(entity_type)
    
    # Set type
    instance["_type"] = entity_type
    
    # Preserve proto_id (if template has 'id', copy it to proto_id)
    if "id" in template and "proto_id" not in instance:
        instance["proto_id"] = template["id"]
    elif "proto_id" not in instance:
        # If no proto_id exists, use the template's _id or generate one
        instance["proto_id"] = template.get("_id", f"proto_{entity_type}")
    
    # Set owner
    if owner_id:
        instance["owner_id"] = owner_id
    
    # Set default status
    if "status" not in instance:
        instance["status"] = "active"
    
    # Merge custom fields
    if custom_fields:
        instance.update(custom_fields)
    
    return instance


def create_multiple_entities(
    template: Dict[str, Any],
    entity_type: str,
    count: int,
    owner_id: Optional[str] = None,
    custom_fields: Optional[Dict[str, Any]] = None
) -> list[Dict[str, Any]]:
    """Create multiple unique entity instances from a template.
    
    Args:
        template: Template/prototype entity
        entity_type: Type of entity
        count: Number of instances to create
        owner_id: Optional owner ID
        custom_fields: Optional fields to add to all instances
        
    Returns:
        List of unique entity instances
        
    Example:
        >>> template = {"proto_id": "common_card", "attack": 10}
        >>> cards = create_multiple_entities(template, "card", count=3, owner_id="player_1")
        >>> len(cards)
        3
        >>> cards[0]["_id"] != cards[1]["_id"]
        True
    """
    return [
        create_unique_entity(template, entity_type, owner_id, custom_fields)
        for _ in range(count)
    ]


def get_proto_id(entity: Dict[str, Any]) -> str:
    """Get the prototype ID of an entity instance.
    
    Args:
        entity: Entity instance
        
    Returns:
        Prototype ID
        
    Example:
        >>> card = {"_id": "card_abc123", "proto_id": "dragon_card"}
        >>> get_proto_id(card)
        'dragon_card'
    """
    return entity.get("proto_id", entity.get("id", "unknown"))


def is_same_prototype(entity1: Dict[str, Any], entity2: Dict[str, Any]) -> bool:
    """Check if two entities are instances of the same prototype.
    
    Args:
        entity1: First entity
        entity2: Second entity
        
    Returns:
        True if both entities have the same proto_id
        
    Example:
        >>> card1 = {"_id": "card_1", "proto_id": "dragon"}
        >>> card2 = {"_id": "card_2", "proto_id": "dragon"}
        >>> card3 = {"_id": "card_3", "proto_id": "goblin"}
        >>> is_same_prototype(card1, card2)
        True
        >>> is_same_prototype(card1, card3)
        False
    """
    return get_proto_id(entity1) == get_proto_id(entity2)


def group_by_prototype(
    entities: list[Dict[str, Any]]
) -> Dict[str, list[Dict[str, Any]]]:
    """Group entity instances by their prototype ID.
    
    Useful for inventory displays or card collection views.
    
    Args:
        entities: List of entity instances
        
    Returns:
        Dictionary mapping proto_id -> list of instances
        
    Example:
        >>> entities = [
        ...     {"_id": "c1", "proto_id": "dragon"},
        ...     {"_id": "c2", "proto_id": "dragon"},
        ...     {"_id": "c3", "proto_id": "goblin"}
        ... ]
        >>> grouped = group_by_prototype(entities)
        >>> len(grouped["dragon"])
        2
        >>> len(grouped["goblin"])
        1
    """
    grouped: Dict[str, list[Dict[str, Any]]] = {}
    
    for entity in entities:
        proto_id = get_proto_id(entity)
        if proto_id not in grouped:
            grouped[proto_id] = []
        grouped[proto_id].append(entity)
    
    return grouped


def count_by_prototype(entities: list[Dict[str, Any]]) -> Dict[str, int]:
    """Count entity instances by prototype.
    
    Args:
        entities: List of entity instances
        
    Returns:
        Dictionary mapping proto_id -> count
        
    Example:
        >>> entities = [
        ...     {"_id": "c1", "proto_id": "dragon"},
        ...     {"_id": "c2", "proto_id": "dragon"},
        ...     {"_id": "c3", "proto_id": "goblin"}
        ... ]
        >>> counts = count_by_prototype(entities)
        >>> counts["dragon"]
        2
        >>> counts["goblin"]
        1
    """
    grouped = group_by_prototype(entities)
    return {proto_id: len(instances) for proto_id, instances in grouped.items()}


class UniqueEntityManager:
    """Manager for creating and tracking unique entity instances.
    
    Useful for game modules that need to spawn unique entities.
    
    Example:
        >>> manager = UniqueEntityManager()
        >>> card = manager.spawn_from_template(
        ...     {"proto_id": "dragon", "attack": 100},
        ...     "card",
        ...     owner_id="player_1"
        ... )
        >>> manager.get_spawn_count()
        1
    """
    
    def __init__(self):
        """Initialize manager with empty spawn tracking."""
        self.spawn_count = 0
        self.spawned_ids: list[str] = []
    
    def spawn_from_template(
        self,
        template: Dict[str, Any],
        entity_type: str,
        owner_id: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Spawn a unique entity and track it.
        
        Args:
            template: Template entity
            entity_type: Entity type
            owner_id: Optional owner
            custom_fields: Optional custom fields
            
        Returns:
            Unique entity instance
        """
        entity = create_unique_entity(template, entity_type, owner_id, custom_fields)
        self.spawn_count += 1
        self.spawned_ids.append(entity["_id"])
        return entity
    
    def spawn_multiple(
        self,
        template: Dict[str, Any],
        entity_type: str,
        count: int,
        owner_id: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> list[Dict[str, Any]]:
        """Spawn multiple unique entities.
        
        Args:
            template: Template entity
            entity_type: Entity type
            count: Number to spawn
            owner_id: Optional owner
            custom_fields: Optional custom fields
            
        Returns:
            List of unique entity instances
        """
        entities = []
        for _ in range(count):
            entity = self.spawn_from_template(
                template, entity_type, owner_id, custom_fields
            )
            entities.append(entity)
        return entities
    
    def get_spawn_count(self) -> int:
        """Get total number of spawned entities.
        
        Returns:
            Spawn count
        """
        return self.spawn_count
    
    def get_spawned_ids(self) -> list[str]:
        """Get list of all spawned entity IDs.
        
        Returns:
            List of entity IDs
        """
        return self.spawned_ids.copy()
    
    def clear_tracking(self) -> None:
        """Clear spawn tracking data."""
        self.spawn_count = 0
        self.spawned_ids.clear()

