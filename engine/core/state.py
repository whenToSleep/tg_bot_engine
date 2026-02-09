"""State module - In-memory game state management.

GameState provides a simple in-memory storage for game entities.
In future iterations, this will be backed by persistent storage.
"""

from typing import Any, Optional


class GameState:
    """In-memory game state manager.
    
    Stores all game entities (players, mobs, items, etc.) in memory.
    Each entity is identified by a unique string ID.
    
    Attributes:
        _entities: Internal dictionary storing all entities
        
    Example:
        >>> state = GameState()
        >>> state.set_entity("player_1", {"gold": 100, "level": 5})
        >>> player = state.get_entity("player_1")
        >>> print(player['gold'])
        100
    """
    
    def __init__(self) -> None:
        """Initialize empty game state."""
        self._entities: dict[str, dict[str, Any]] = {}
    
    def get_entity(self, entity_id: str) -> Optional[dict[str, Any]]:
        """Get entity by ID.
        
        Args:
            entity_id: Unique identifier of the entity
            
        Returns:
            Entity data dictionary or None if not found
        """
        return self._entities.get(entity_id)
    
    def set_entity(self, entity_id: str, data: dict[str, Any]) -> None:
        """Set or update entity data.
        
        Args:
            entity_id: Unique identifier of the entity
            data: Entity data dictionary
            
        Note:
            If entity exists, it will be replaced completely.
            Use get_entity() + modify + set_entity() pattern for updates.
        """
        self._entities[entity_id] = data
    
    def delete_entity(self, entity_id: str) -> None:
        """Delete entity by ID.
        
        Args:
            entity_id: Unique identifier of the entity
            
        Note:
            Does nothing if entity doesn't exist (idempotent).
        """
        self._entities.pop(entity_id, None)
    
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists.
        
        Args:
            entity_id: Unique identifier of the entity
            
        Returns:
            True if entity exists, False otherwise
        """
        return entity_id in self._entities
    
    def clear(self) -> None:
        """Clear all entities from state.
        
        Note:
            Use with caution - this removes all game data!
        """
        self._entities.clear()
    
    def entity_count(self) -> int:
        """Get total number of entities.
        
        Returns:
            Number of entities currently stored
        """
        return len(self._entities)

