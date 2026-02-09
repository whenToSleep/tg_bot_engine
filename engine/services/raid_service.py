"""Raid Service - Global boss system for multiplayer cooperative raids.

This module provides a World Raid system where multiple players attack shared bosses:
- Shared entity with millions/billions of HP
- Concurrent damage tracking with optimistic locking
- Automatic retry on conflicts
- Reward distribution based on contribution
- Leaderboards and rankings

Designed for MMO-style raid events where thousands of players cooperate.

Example:
    >>> from engine.services.raid_service import RaidService, get_raid_service
    >>> 
    >>> # Initialize raid service
    >>> service = get_raid_service()
    >>> 
    >>> # Create a world boss
    >>> boss = service.create_raid(
    ...     raid_id="dragon_raid_001",
    ...     name="Ancient Dragon",
    ...     max_hp=1_000_000_000,  # 1 billion HP!
    ...     duration_hours=48
    ... )
    >>> 
    >>> # Player attacks
    >>> result = await service.attack_raid(
    ...     raid_id="dragon_raid_001",
    ...     player_id="player_123",
    ...     damage=15000
    ... )
    >>> 
    >>> # Check raid status
    >>> status = service.get_raid_status("dragon_raid_001")
    >>> print(f"HP: {status['current_hp']} / {status['max_hp']}")
    >>> print(f"Participants: {status['participant_count']}")
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
from engine.core.state import GameState

logger = logging.getLogger(__name__)


class RaidStatus(str, Enum):
    """Status of a raid event."""
    SCHEDULED = "scheduled"  # Not yet started
    ACTIVE = "active"        # Currently attackable
    COMPLETED = "completed"  # Boss defeated
    EXPIRED = "expired"      # Time ran out
    CANCELLED = "cancelled"  # Manually cancelled


@dataclass
class RaidEntity:
    """Shared raid entity (world boss).
    
    Attributes:
        raid_id: Unique raid identifier
        name: Display name of the boss
        description: Raid description/lore
        max_hp: Maximum HP (can be billions)
        current_hp: Current HP (decreases with attacks)
        status: Current raid status
        created_at: When raid was created
        started_at: When raid became active
        expires_at: When raid will expire
        version: Optimistic lock version for concurrent updates
        participants: Dictionary of player_id -> contribution data
        total_damage_dealt: Total damage across all players
        reward_pool: Rewards available for distribution
    """
    raid_id: str
    name: str
    description: str
    max_hp: int
    current_hp: int
    status: RaidStatus = RaidStatus.SCHEDULED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    version: int = 0  # For optimistic locking
    participants: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    total_damage_dealt: int = 0
    reward_pool: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "_type": "raid",
            "_id": self.raid_id,
            "name": self.name,
            "description": self.description,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "version": self.version,
            "participants": self.participants,
            "total_damage_dealt": self.total_damage_dealt,
            "reward_pool": self.reward_pool
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "RaidEntity":
        """Create RaidEntity from dictionary."""
        return RaidEntity(
            raid_id=data["_id"],
            name=data["name"],
            description=data["description"],
            max_hp=data["max_hp"],
            current_hp=data["current_hp"],
            status=RaidStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            version=data.get("version", 0),
            participants=data.get("participants", {}),
            total_damage_dealt=data.get("total_damage_dealt", 0),
            reward_pool=data.get("reward_pool", {})
        )


@dataclass
class AttackResult:
    """Result of a raid attack.
    
    Attributes:
        success: Whether attack succeeded
        damage_dealt: Actual damage dealt
        current_hp: Raid boss current HP after attack
        max_hp: Raid boss max HP
        percentage: HP percentage (0-100)
        raid_defeated: Whether this attack defeated the boss
        rank: Player's rank among participants
        total_contribution: Player's total damage
        retry_count: Number of retries needed (for optimistic locking)
        error_message: Optional error message
    """
    success: bool
    damage_dealt: int = 0
    current_hp: int = 0
    max_hp: int = 0
    percentage: float = 0.0
    raid_defeated: bool = False
    rank: int = 0
    total_contribution: int = 0
    retry_count: int = 0
    error_message: Optional[str] = None


class RaidService:
    """Service for managing global raid events.
    
    Features:
    - Create time-limited raid events
    - Handle concurrent attacks with optimistic locking
    - Automatic retry on version conflicts
    - Track participant contributions
    - Generate leaderboards
    - Distribute rewards based on contribution
    
    Example:
        >>> service = RaidService()
        >>> 
        >>> # Create raid
        >>> raid_id = service.create_raid(
        ...     raid_id="fire_dragon",
        ...     name="Fire Dragon Lord",
        ...     max_hp=5_000_000_000,
        ...     duration_hours=24
        ... )
        >>> 
        >>> # Activate raid
        >>> service.activate_raid(raid_id)
        >>> 
        >>> # Player attacks (async)
        >>> result = await service.attack_raid(
        ...     raid_id="fire_dragon",
        ...     player_id="player_1",
        ...     damage=25000
        ... )
    """
    
    MAX_RETRY_ATTEMPTS = 5  # Max retries for optimistic locking
    RETRY_DELAY = 0.05  # Delay between retries (seconds)
    
    def __init__(self, state: Optional[GameState] = None):
        """Initialize raid service.
        
        Args:
            state: Optional GameState for persistence
        """
        self._state = state
        self._raid_cache: Dict[str, RaidEntity] = {}
    
    def create_raid(
        self,
        raid_id: str,
        name: str,
        description: str,
        max_hp: int,
        duration_hours: float = 48.0,
        reward_pool: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new raid event.
        
        Args:
            raid_id: Unique raid identifier
            name: Boss name
            description: Raid description
            max_hp: Maximum HP (can be billions)
            duration_hours: How long raid stays active
            reward_pool: Optional rewards for participants
            
        Returns:
            raid_id
            
        Raises:
            ValueError: If raid already exists
            
        Example:
            >>> service.create_raid(
            ...     raid_id="golem_raid",
            ...     name="Stone Golem",
            ...     description="A massive stone guardian",
            ...     max_hp=10_000_000_000,  # 10 billion HP
            ...     duration_hours=72
            ... )
        """
        if raid_id in self._raid_cache:
            raise ValueError(f"Raid '{raid_id}' already exists")
        
        # Check state
        if self._state and self._state.exists(raid_id):
            raise ValueError(f"Raid '{raid_id}' already exists in state")
        
        # Create raid entity
        raid = RaidEntity(
            raid_id=raid_id,
            name=name,
            description=description,
            max_hp=max_hp,
            current_hp=max_hp,
            status=RaidStatus.SCHEDULED,
            expires_at=datetime.now() + timedelta(hours=duration_hours),
            reward_pool=reward_pool or {}
        )
        
        # Cache and persist
        self._raid_cache[raid_id] = raid
        if self._state:
            self._state.set_entity(raid_id, raid.to_dict())
        
        logger.info(
            f"Created raid '{raid_id}' ({name}) with {max_hp:,} HP, "
            f"duration: {duration_hours}h"
        )
        
        return raid_id
    
    def activate_raid(self, raid_id: str) -> None:
        """Activate a raid (make it attackable).
        
        Args:
            raid_id: Raid to activate
            
        Raises:
            ValueError: If raid not found or already completed
        """
        raid = self._get_raid(raid_id)
        
        if raid.status == RaidStatus.COMPLETED:
            raise ValueError(f"Raid '{raid_id}' already completed")
        
        if raid.status == RaidStatus.EXPIRED:
            raise ValueError(f"Raid '{raid_id}' has expired")
        
        raid.status = RaidStatus.ACTIVE
        raid.started_at = datetime.now()
        
        self._save_raid(raid)
        logger.info(f"Activated raid '{raid_id}'")
    
    async def attack_raid(
        self,
        raid_id: str,
        player_id: str,
        damage: int,
        player_data: Optional[Dict[str, Any]] = None
    ) -> AttackResult:
        """Attack a raid boss (with optimistic locking and retry).
        
        This method handles concurrent attacks from thousands of players by:
        1. Loading current raid state
        2. Attempting to apply damage
        3. Checking version for conflicts
        4. Retrying on conflict (up to MAX_RETRY_ATTEMPTS)
        
        Args:
            raid_id: Raid to attack
            player_id: ID of attacking player
            damage: Damage to deal
            player_data: Optional player info for tracking
            
        Returns:
            AttackResult with outcome
            
        Example:
            >>> result = await service.attack_raid(
            ...     raid_id="dragon",
            ...     player_id="player_123",
            ...     damage=50000
            ... )
            >>> if result.success:
            ...     print(f"Dealt {result.damage_dealt} damage!")
            ...     print(f"Boss HP: {result.current_hp}/{result.max_hp}")
        """
        retry_count = 0
        last_error = None
        
        # Retry loop for optimistic locking
        while retry_count < self.MAX_RETRY_ATTEMPTS:
            try:
                # Load current raid state
                raid = self._get_raid(raid_id)
                
                # Validate raid status
                if raid.status != RaidStatus.ACTIVE:
                    return AttackResult(
                        success=False,
                        error_message=f"Raid is not active (status: {raid.status.value})"
                    )
                
                # Check expiration
                if raid.expires_at and datetime.now() > raid.expires_at:
                    raid.status = RaidStatus.EXPIRED
                    self._save_raid(raid)
                    return AttackResult(
                        success=False,
                        error_message="Raid has expired"
                    )
                
                # Store current version for optimistic locking
                expected_version = raid.version
                
                # Calculate actual damage (can't go below 0)
                actual_damage = min(damage, raid.current_hp)
                
                # Apply damage
                raid.current_hp -= actual_damage
                raid.total_damage_dealt += actual_damage
                raid.version += 1  # Increment version
                
                # Track participant contribution
                if player_id not in raid.participants:
                    raid.participants[player_id] = {
                        "player_id": player_id,
                        "total_damage": 0,
                        "attack_count": 0,
                        "first_attack": datetime.now().isoformat(),
                        "last_attack": datetime.now().isoformat()
                    }
                    if player_data:
                        raid.participants[player_id].update(player_data)
                
                participant = raid.participants[player_id]
                participant["total_damage"] += actual_damage
                participant["attack_count"] += 1
                participant["last_attack"] = datetime.now().isoformat()
                
                # Check if boss defeated
                raid_defeated = raid.current_hp <= 0
                if raid_defeated:
                    raid.status = RaidStatus.COMPLETED
                    logger.info(f"Raid '{raid_id}' completed! Defeated by {len(raid.participants)} players")
                
                # Optimistic locking: check version before saving
                if self._state:
                    current_data = self._state.get_entity(raid_id)
                    if current_data and current_data.get("version", 0) != expected_version:
                        # Version conflict - retry
                        retry_count += 1
                        logger.debug(
                            f"Version conflict on raid '{raid_id}' "
                            f"(expected {expected_version}, got {current_data.get('version')}). "
                            f"Retry {retry_count}/{self.MAX_RETRY_ATTEMPTS}"
                        )
                        await asyncio.sleep(self.RETRY_DELAY)
                        continue
                
                # Save raid state
                self._save_raid(raid)
                
                # Calculate player rank
                rank = self._calculate_rank(raid, player_id)
                
                # Success!
                return AttackResult(
                    success=True,
                    damage_dealt=actual_damage,
                    current_hp=raid.current_hp,
                    max_hp=raid.max_hp,
                    percentage=(raid.current_hp / raid.max_hp * 100) if raid.max_hp > 0 else 0,
                    raid_defeated=raid_defeated,
                    rank=rank,
                    total_contribution=participant["total_damage"],
                    retry_count=retry_count
                )
                
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                logger.error(
                    f"Error attacking raid '{raid_id}': {e}. "
                    f"Retry {retry_count}/{self.MAX_RETRY_ATTEMPTS}"
                )
                await asyncio.sleep(self.RETRY_DELAY)
        
        # Max retries exceeded
        return AttackResult(
            success=False,
            error_message=f"Max retries exceeded: {last_error}",
            retry_count=retry_count
        )
    
    def get_raid_status(self, raid_id: str) -> Dict[str, Any]:
        """Get current raid status.
        
        Args:
            raid_id: Raid to query
            
        Returns:
            Dictionary with raid status
            
        Example:
            >>> status = service.get_raid_status("dragon_raid")
            >>> print(f"HP: {status['current_hp']:,} / {status['max_hp']:,}")
            >>> print(f"Progress: {status['progress_percentage']:.2f}%")
            >>> print(f"Participants: {status['participant_count']}")
        """
        raid = self._get_raid(raid_id)
        
        progress = ((raid.max_hp - raid.current_hp) / raid.max_hp * 100) if raid.max_hp > 0 else 0
        
        return {
            "raid_id": raid.raid_id,
            "name": raid.name,
            "description": raid.description,
            "status": raid.status.value,
            "current_hp": raid.current_hp,
            "max_hp": raid.max_hp,
            "progress_percentage": progress,
            "total_damage_dealt": raid.total_damage_dealt,
            "participant_count": len(raid.participants),
            "started_at": raid.started_at.isoformat() if raid.started_at else None,
            "expires_at": raid.expires_at.isoformat() if raid.expires_at else None,
            "time_remaining": self._calculate_time_remaining(raid)
        }
    
    def get_leaderboard(
        self,
        raid_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get raid damage leaderboard.
        
        Args:
            raid_id: Raid to query
            limit: Max entries to return
            
        Returns:
            List of participant data sorted by contribution
            
        Example:
            >>> leaderboard = service.get_leaderboard("dragon_raid", limit=10)
            >>> for i, entry in enumerate(leaderboard, 1):
            ...     print(f"{i}. {entry['player_id']}: {entry['total_damage']:,} damage")
        """
        raid = self._get_raid(raid_id)
        
        # Sort participants by damage
        sorted_participants = sorted(
            raid.participants.values(),
            key=lambda p: p["total_damage"],
            reverse=True
        )
        
        # Add rank and percentage
        leaderboard = []
        for rank, participant in enumerate(sorted_participants[:limit], 1):
            contribution_percentage = (
                (participant["total_damage"] / raid.total_damage_dealt * 100)
                if raid.total_damage_dealt > 0 else 0
            )
            
            leaderboard.append({
                "rank": rank,
                "player_id": participant["player_id"],
                "total_damage": participant["total_damage"],
                "attack_count": participant["attack_count"],
                "contribution_percentage": contribution_percentage,
                "first_attack": participant["first_attack"],
                "last_attack": participant["last_attack"]
            })
        
        return leaderboard
    
    def get_player_contribution(
        self,
        raid_id: str,
        player_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific player's contribution to a raid.
        
        Args:
            raid_id: Raid to query
            player_id: Player to query
            
        Returns:
            Player contribution data or None if not participated
        """
        raid = self._get_raid(raid_id)
        
        if player_id not in raid.participants:
            return None
        
        participant = raid.participants[player_id]
        rank = self._calculate_rank(raid, player_id)
        
        contribution_percentage = (
            (participant["total_damage"] / raid.total_damage_dealt * 100)
            if raid.total_damage_dealt > 0 else 0
        )
        
        return {
            "raid_id": raid_id,
            "player_id": player_id,
            "total_damage": participant["total_damage"],
            "attack_count": participant["attack_count"],
            "rank": rank,
            "contribution_percentage": contribution_percentage,
            "first_attack": participant["first_attack"],
            "last_attack": participant["last_attack"]
        }
    
    def _get_raid(self, raid_id: str) -> RaidEntity:
        """Get raid from cache or state.
        
        Args:
            raid_id: Raid ID
            
        Returns:
            RaidEntity
            
        Raises:
            ValueError: If raid not found
        """
        # Check cache
        if raid_id in self._raid_cache:
            return self._raid_cache[raid_id]
        
        # Load from state
        if self._state:
            raid_data = self._state.get_entity(raid_id)
            if raid_data:
                raid = RaidEntity.from_dict(raid_data)
                self._raid_cache[raid_id] = raid
                return raid
        
        raise ValueError(f"Raid '{raid_id}' not found")
    
    def _save_raid(self, raid: RaidEntity) -> None:
        """Save raid to cache and state."""
        self._raid_cache[raid.raid_id] = raid
        
        if self._state:
            self._state.set_entity(raid.raid_id, raid.to_dict())
    
    def _calculate_rank(self, raid: RaidEntity, player_id: str) -> int:
        """Calculate player's rank in raid leaderboard."""
        if player_id not in raid.participants:
            return len(raid.participants) + 1
        
        player_damage = raid.participants[player_id]["total_damage"]
        
        # Count how many players have more damage
        rank = 1
        for participant in raid.participants.values():
            if participant["player_id"] != player_id and participant["total_damage"] > player_damage:
                rank += 1
        
        return rank
    
    def _calculate_time_remaining(self, raid: RaidEntity) -> Optional[str]:
        """Calculate human-readable time remaining."""
        if not raid.expires_at:
            return None
        
        remaining = raid.expires_at - datetime.now()
        if remaining.total_seconds() <= 0:
            return "Expired"
        
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


# Global singleton instance
_global_raid_service: Optional[RaidService] = None


def get_raid_service(state: Optional[GameState] = None) -> RaidService:
    """Get the global raid service instance.
    
    Args:
        state: Optional GameState for first initialization
    
    Returns:
        Global RaidService instance
        
    Example:
        >>> from engine.services.raid_service import get_raid_service
        >>> service = get_raid_service()
    """
    global _global_raid_service
    if _global_raid_service is None:
        _global_raid_service = RaidService(state)
    return _global_raid_service


def reset_raid_service() -> None:
    """Reset the global raid service instance.
    
    Used primarily for testing.
    """
    global _global_raid_service
    _global_raid_service = None

