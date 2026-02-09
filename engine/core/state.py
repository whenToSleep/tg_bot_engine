"""State module - In-memory game state management.

GameState provides a simple in-memory storage for game entities.
In future iterations, this will be backed by persistent storage.
"""

from typing import Any, Optional, List, Callable


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
    
    def get_entities_by_type(self, entity_type: str) -> List[dict[str, Any]]:
        """Get all entities of a specific type.
        
        Args:
            entity_type: Type identifier (value of "_type" field)
            
        Returns:
            List of all entities matching the type
            
        Example:
            >>> state.set_entity("player_1", {"_type": "player", "name": "Alice"})
            >>> state.set_entity("player_2", {"_type": "player", "name": "Bob"})
            >>> state.set_entity("mob_1", {"_type": "mob", "name": "Goblin"})
            >>> players = state.get_entities_by_type("player")
            >>> print(len(players))
            2
            
        Note:
            This iterates through all entities (O(n) complexity).
            For large entity counts, consider using persistent storage with indexes.
        """
        return [
            entity for entity in self._entities.values()
            if entity.get("_type") == entity_type
        ]
    
    def get_entities_by_filter(
        self, 
        filter_func: Callable[[dict[str, Any]], bool]
    ) -> List[dict[str, Any]]:
        """Get entities matching a custom filter function.
        
        Args:
            filter_func: Function that takes entity dict and returns bool
            
        Returns:
            List of entities where filter_func returns True
            
        Example:
            >>> state.set_entity("p1", {"_type": "player", "level": 10, "gold": 500})
            >>> state.set_entity("p2", {"_type": "player", "level": 5, "gold": 100})
            >>> rich_players = state.get_entities_by_filter(
            ...     lambda e: e.get("_type") == "player" and e.get("gold", 0) > 200
            ... )
            >>> print(len(rich_players))
            1
            
        Note:
            This is more flexible than get_entities_by_type() but may be slower.
        """
        return [entity for entity in self._entities.values() if filter_func(entity)]
    
    def get_all_entities(self) -> dict[str, dict[str, Any]]:
        """Get all entities as a dictionary.
        
        Returns:
            Dict mapping entity_id -> entity_data
            
        Warning:
            Returns a reference to internal storage. Modifying returned dict
            directly will affect state. Use with caution or make a copy.
            
        Example:
            >>> all_entities = state.get_all_entities()
            >>> for entity_id, entity_data in all_entities.items():
            ...     print(f"{entity_id}: {entity_data['_type']}")
        """
        return self._entities

