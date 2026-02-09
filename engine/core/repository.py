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
    
    # Referral System Methods (v0.6.0+)
    
    @abstractmethod
    def get_referral_tree(
        self,
        player_id: str,
        depth: int = 1,
        include_stats: bool = False
    ) -> Dict[str, Any]:
        """Get referral tree for a player.
        
        Retrieves the referral network starting from a player,
        going down N levels deep. Useful for calculating referral bonuses.
        
        Args:
            player_id: Root player ID
            depth: How many levels deep to traverse (1 = direct referrals only)
            include_stats: Whether to include aggregated stats
            
        Returns:
            Dictionary with referral tree structure:
            {
                "player_id": str,
                "direct_referrals": List[str],  # Direct referrals
                "total_referrals": int,  # Total across all levels
                "referral_tree": {
                    "level_1": List[str],  # Direct referrals
                    "level_2": List[str],  # Referrals of referrals
                    ...
                },
                "stats": {  # If include_stats=True
                    "total_spending": int,
                    "active_referrals": int,
                    ...
                }
            }
            
        Example:
            >>> tree = repo.get_referral_tree("player_1", depth=2)
            >>> print(f"Direct referrals: {tree['direct_referrals']}")
            >>> print(f"Total referrals: {tree['total_referrals']}")
        """
        pass
    
    @abstractmethod
    def add_referral(
        self,
        referrer_id: str,
        referred_id: str
    ) -> bool:
        """Create a referral link between two players.
        
        Args:
            referrer_id: Player who referred
            referred_id: Player who was referred
            
        Returns:
            True if link created, False if already exists
            
        Raises:
            ValueError: If either player doesn't exist
            
        Example:
            >>> repo.add_referral("player_veteran", "player_newbie")
            True
        """
        pass
    
    @abstractmethod
    def get_referrer(self, player_id: str) -> Optional[str]:
        """Get the player who referred this player.
        
        Args:
            player_id: Player to query
            
        Returns:
            Referrer's player ID or None
            
        Example:
            >>> referrer = repo.get_referrer("player_newbie")
            >>> print(f"Referred by: {referrer}")
        """
        pass
    
    @abstractmethod
    def get_direct_referrals(self, player_id: str) -> List[str]:
        """Get list of players directly referred by this player.
        
        Args:
            player_id: Player to query
            
        Returns:
            List of referred player IDs
            
        Example:
            >>> referrals = repo.get_direct_referrals("player_veteran")
            >>> print(f"Has {len(referrals)} direct referrals")
        """
        pass

