"""Entity Status System - Track entity states for complex game mechanics.

This module provides status tracking for entities to prevent conflicts in:
- Trading systems (cards on auction can't be used in battle)
- Equipment systems (equipped items can't be traded)
- Lock mechanisms (admin-locked entities)

Example:
    >>> from engine.core.entity_status import EntityStatus, set_status, has_status
    >>> 
    >>> card = {"_id": "card_123", "status": "active"}
    >>> set_status(card, EntityStatus.ON_AUCTION)
    >>> has_status(card, EntityStatus.ON_AUCTION)
    True
"""

from typing import Dict, Any, List
from enum import Enum


class EntityStatus(Enum):
    """Possible entity statuses.
    
    Attributes:
        ACTIVE: Normal state, entity can be used
        LOCKED: Admin-locked, cannot be modified
        ON_AUCTION: Listed on marketplace, cannot be used
        IN_TRADE: Part of pending trade, cannot be modified
        EQUIPPED: Equipped by player, cannot be traded
        CONSUMED: Used up, pending deletion
        RESERVED: Reserved for specific action
    """
    ACTIVE = "active"
    LOCKED = "locked"
    ON_AUCTION = "on_auction"
    IN_TRADE = "in_trade"
    EQUIPPED = "equipped"
    CONSUMED = "consumed"
    RESERVED = "reserved"


def set_status(entity: Dict[str, Any], status: EntityStatus) -> None:
    """Set entity status.
    
    Args:
        entity: Entity to modify
        status: New status
        
    Example:
        >>> card = {"_id": "card_1"}
        >>> set_status(card, EntityStatus.ON_AUCTION)
        >>> card["status"]
        'on_auction'
    """
    entity["status"] = status.value


def get_status(entity: Dict[str, Any]) -> EntityStatus:
    """Get entity status.
    
    Args:
        entity: Entity to check
        
    Returns:
        Current status (defaults to ACTIVE if not set)
        
    Example:
        >>> card = {"status": "on_auction"}
        >>> get_status(card)
        <EntityStatus.ON_AUCTION: 'on_auction'>
    """
    status_value = entity.get("status", "active")
    return EntityStatus(status_value)


def has_status(entity: Dict[str, Any], status: EntityStatus) -> bool:
    """Check if entity has a specific status.
    
    Args:
        entity: Entity to check
        status: Status to check for
        
    Returns:
        True if entity has this status
        
    Example:
        >>> card = {"status": "on_auction"}
        >>> has_status(card, EntityStatus.ON_AUCTION)
        True
        >>> has_status(card, EntityStatus.ACTIVE)
        False
    """
    return get_status(entity) == status


def is_usable(entity: Dict[str, Any]) -> bool:
    """Check if entity can be used in game actions.
    
    Entities are NOT usable if they are:
    - ON_AUCTION
    - IN_TRADE
    - LOCKED
    - CONSUMED
    
    Args:
        entity: Entity to check
        
    Returns:
        True if entity can be used
        
    Example:
        >>> card = {"status": "active"}
        >>> is_usable(card)
        True
        >>> set_status(card, EntityStatus.ON_AUCTION)
        >>> is_usable(card)
        False
    """
    status = get_status(entity)
    unusable_statuses = {
        EntityStatus.ON_AUCTION,
        EntityStatus.IN_TRADE,
        EntityStatus.LOCKED,
        EntityStatus.CONSUMED
    }
    return status not in unusable_statuses


def is_tradable(entity: Dict[str, Any]) -> bool:
    """Check if entity can be traded.
    
    Entities are NOT tradable if they are:
    - ON_AUCTION (already listed)
    - IN_TRADE (already in a trade)
    - LOCKED (admin-locked)
    - EQUIPPED (currently equipped)
    - CONSUMED (used up)
    
    Args:
        entity: Entity to check
        
    Returns:
        True if entity can be traded
        
    Example:
        >>> card = {"status": "active"}
        >>> is_tradable(card)
        True
        >>> set_status(card, EntityStatus.EQUIPPED)
        >>> is_tradable(card)
        False
    """
    status = get_status(entity)
    non_tradable_statuses = {
        EntityStatus.ON_AUCTION,
        EntityStatus.IN_TRADE,
        EntityStatus.LOCKED,
        EntityStatus.EQUIPPED,
        EntityStatus.CONSUMED
    }
    return status not in non_tradable_statuses


def get_entities_by_status(
    entities: Dict[str, Dict[str, Any]], 
    status: EntityStatus
) -> List[Dict[str, Any]]:
    """Filter entities by status.
    
    Args:
        entities: Dictionary of entities (id -> entity)
        status: Status to filter by
        
    Returns:
        List of entities with specified status
        
    Example:
        >>> entities = {
        ...     "card_1": {"status": "active"},
        ...     "card_2": {"status": "on_auction"},
        ...     "card_3": {"status": "active"}
        ... }
        >>> active = get_entities_by_status(entities, EntityStatus.ACTIVE)
        >>> len(active)
        2
    """
    return [
        entity for entity in entities.values()
        if get_status(entity) == status
    ]


def filter_usable(entities: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter only usable entities.
    
    Convenience function for getting entities that can be used in game.
    
    Args:
        entities: Dictionary of entities
        
    Returns:
        List of usable entities
        
    Example:
        >>> entities = {
        ...     "card_1": {"status": "active"},
        ...     "card_2": {"status": "on_auction"}
        ... }
        >>> usable = filter_usable(entities)
        >>> len(usable)
        1
    """
    return [
        entity for entity in entities.values()
        if is_usable(entity)
    ]


def filter_tradable(entities: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter only tradable entities.
    
    Convenience function for getting entities that can be traded.
    
    Args:
        entities: Dictionary of entities
        
    Returns:
        List of tradable entities
        
    Example:
        >>> entities = {
        ...     "card_1": {"status": "active"},
        ...     "card_2": {"status": "equipped"}
        ... }
        >>> tradable = filter_tradable(entities)
        >>> len(tradable)
        1
    """
    return [
        entity for entity in entities.values()
        if is_tradable(entity)
    ]


class StatusValidator:
    """Validator for checking entity status before actions.
    
    Useful for Commands that need to verify entity status.
    
    Example:
        >>> validator = StatusValidator()
        >>> card = {"_id": "card_1", "status": "on_auction"}
        >>> 
        >>> try:
        ...     validator.require_usable(card, "Cannot use card in battle")
        ... except ValueError as e:
        ...     print(e)
        'Cannot use card in battle: entity is on_auction'
    """
    
    @staticmethod
    def require_status(
        entity: Dict[str, Any],
        required_status: EntityStatus,
        error_msg: str = "Invalid entity status"
    ) -> None:
        """Require entity to have specific status.
        
        Args:
            entity: Entity to check
            required_status: Required status
            error_msg: Error message prefix
            
        Raises:
            ValueError: If entity doesn't have required status
        """
        if not has_status(entity, required_status):
            current = get_status(entity).value
            raise ValueError(
                f"{error_msg}: expected {required_status.value}, got {current}"
            )
    
    @staticmethod
    def require_usable(
        entity: Dict[str, Any],
        error_msg: str = "Entity cannot be used"
    ) -> None:
        """Require entity to be usable.
        
        Args:
            entity: Entity to check
            error_msg: Error message
            
        Raises:
            ValueError: If entity is not usable
        """
        if not is_usable(entity):
            status = get_status(entity).value
            raise ValueError(f"{error_msg}: entity is {status}")
    
    @staticmethod
    def require_tradable(
        entity: Dict[str, Any],
        error_msg: str = "Entity cannot be traded"
    ) -> None:
        """Require entity to be tradable.
        
        Args:
            entity: Entity to check
            error_msg: Error message
            
        Raises:
            ValueError: If entity is not tradable
        """
        if not is_tradable(entity):
            status = get_status(entity).value
            raise ValueError(f"{error_msg}: entity is {status}")

