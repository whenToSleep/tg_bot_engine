"""Abstract repository pattern for entity persistence.

This module defines the abstract interface for storing and retrieving
game entities from persistent storage (database, file system, etc).
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class EntityRepository(ABC):
    """Abstract repository for entity persistence.
    
    Defines the interface that all concrete repository implementations
    must follow. Supports basic CRUD operations and batch operations.
    """
    
    @abstractmethod
    def save(self, entity_id: str, entity_data: dict) -> None:
        """Save an entity to persistent storage.
        
        Args:
            entity_id: Unique identifier of the entity
            entity_data: Dictionary containing entity data
            
        Raises:
            ValueError: If optimistic locking fails
        """
        pass
    
    @abstractmethod
    def load(self, entity_id: str) -> Optional[dict]:
        """Load an entity from persistent storage.
        
        Args:
            entity_id: Unique identifier of the entity
            
        Returns:
            Dictionary with entity data, or None if not found
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> None:
        """Delete an entity from persistent storage.
        
        Args:
            entity_id: Unique identifier of the entity
        """
        pass
    
    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if an entity exists in persistent storage.
        
        Args:
            entity_id: Unique identifier of the entity
            
        Returns:
            True if entity exists, False otherwise
        """
        pass
    
    @abstractmethod
    def list_by_type(self, entity_type: str) -> List[str]:
        """List all entity IDs of a given type.
        
        Args:
            entity_type: Type of entities to list (e.g., 'player', 'mob')
            
        Returns:
            List of entity IDs
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Count total number of entities in storage.
        
        Returns:
            Number of entities
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all entities from storage.
        
        Warning:
            This operation is destructive and cannot be undone.
        """
        pass

