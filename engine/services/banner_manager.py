"""Banner Manager - Dynamic gacha banner system with hot-swapping.

This module manages gacha banners (card pools) with time-limited availability:
- Create flash banners that auto-activate/expire
- Hot-swap active pools without bot restart
- Track banner history and statistics
- Notify players of new banners via EventBus

Designed for CCG games with rotating banners (e.g., "Rate-Up", "Limited Edition").

Example:
    >>> from engine.services.banner_manager import get_banner_manager
    >>> from engine.core.data_loader import get_data_loader
    >>> 
    >>> manager = get_banner_manager()
    >>> loader = get_data_loader()
    >>> 
    >>> # Create a 2-hour flash banner
    >>> banner_id = manager.create_flash_banner(
    ...     banner_id="fire_rate_up",
    ...     card_pool=loader.get_filtered("card", lambda c: c.get("element") == "fire"),
    ...     custom_weights={"S": 3.0, "SS": 1.0},  # Triple S-rank rate!
    ...     duration_seconds=7200,
    ...     notify_players=True
    ... )
    >>> 
    >>> # Get current active banner
    >>> active = manager.get_active_banner()
    >>> print(active["banner_id"])  # "fire_rate_up"
"""

from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

from engine.services.scheduler import get_scheduler

logger = logging.getLogger(__name__)


class BannerStatus(str, Enum):
    """Status of a gacha banner."""
    SCHEDULED = "scheduled"  # Waiting to activate
    ACTIVE = "active"        # Currently available for pulls
    EXPIRED = "expired"      # Time expired
    CANCELLED = "cancelled"  # Manually cancelled


@dataclass
class BannerConfig:
    """Configuration for a gacha banner.
    
    Attributes:
        banner_id: Unique identifier
        name: Display name for players
        description: Banner description/lore
        card_pool: List of card templates available in this banner
        custom_weights: Optional custom rarity weights (overrides defaults)
        featured_cards: List of featured card IDs (for UI highlighting)
        start_time: When banner activates (None = immediate)
        end_time: When banner expires (None = manual expiration)
        pity_carries_over: Whether pity counter persists after banner ends
        max_pulls_per_player: Optional pull limit per player
    """
    banner_id: str
    name: str
    description: str
    card_pool: List[Dict[str, Any]]
    custom_weights: Optional[Dict[str, float]] = None
    featured_cards: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    pity_carries_over: bool = True
    max_pulls_per_player: Optional[int] = None


@dataclass
class BannerState:
    """Runtime state of a banner.
    
    Tracks banner lifecycle and statistics.
    """
    config: BannerConfig
    status: BannerStatus
    total_pulls: int = 0
    unique_pullers: set = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    activated_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    scheduler_task_id: Optional[str] = None  # For expiration task


class BannerManager:
    """Manages gacha banners with hot-swapping and scheduling.
    
    Features:
    - Create time-limited flash banners
    - Automatic activation/expiration via Scheduler
    - Hot-swap active pools without restart
    - Banner history and statistics
    - Player notifications via EventBus
    
    Example:
        >>> manager = BannerManager()
        >>> 
        >>> # Create permanent banner
        >>> manager.create_banner(
        ...     banner_id="standard",
        ...     name="Standard Banner",
        ...     card_pool=all_cards
        ... )
        >>> manager.activate_banner("standard")
        >>> 
        >>> # Create 2-hour flash banner
        >>> manager.create_flash_banner(
        ...     banner_id="fire_event",
        ...     name="Fire Festival",
        ...     card_pool=fire_cards,
        ...     duration_seconds=7200
        ... )
    """
    
    def __init__(self):
        """Initialize banner manager."""
        self._banners: Dict[str, BannerState] = {}
        self._active_banner_id: Optional[str] = None
        self._default_banner_id: Optional[str] = None
        self._event_callbacks: List[Callable[[str, Dict[str, Any]], Awaitable[None]]] = []
    
    def create_banner(
        self,
        banner_id: str,
        name: str,
        description: str,
        card_pool: List[Dict[str, Any]],
        custom_weights: Optional[Dict[str, float]] = None,
        featured_cards: Optional[List[str]] = None,
        pity_carries_over: bool = True,
        max_pulls_per_player: Optional[int] = None
    ) -> str:
        """Create a new banner (not yet active).
        
        Args:
            banner_id: Unique identifier
            name: Display name
            description: Banner description
            card_pool: List of card templates
            custom_weights: Optional custom rarity weights
            featured_cards: List of featured card IDs
            pity_carries_over: Whether pity persists after expiration
            max_pulls_per_player: Optional pull limit
            
        Returns:
            banner_id
            
        Example:
            >>> manager.create_banner(
            ...     banner_id="standard",
            ...     name="Standard Banner",
            ...     description="Always available",
            ...     card_pool=all_cards
            ... )
        """
        if banner_id in self._banners:
            raise ValueError(f"Banner '{banner_id}' already exists")
        
        if not card_pool:
            raise ValueError("Banner must have at least one card in pool")
        
        config = BannerConfig(
            banner_id=banner_id,
            name=name,
            description=description,
            card_pool=card_pool,
            custom_weights=custom_weights,
            featured_cards=featured_cards or [],
            pity_carries_over=pity_carries_over,
            max_pulls_per_player=max_pulls_per_player
        )
        
        state = BannerState(
            config=config,
            status=BannerStatus.SCHEDULED
        )
        
        self._banners[banner_id] = state
        logger.info(f"Created banner '{banner_id}' ({len(card_pool)} cards)")
        
        return banner_id
    
    def create_flash_banner(
        self,
        banner_id: str,
        name: str,
        description: str,
        card_pool: List[Dict[str, Any]],
        duration_seconds: float,
        custom_weights: Optional[Dict[str, float]] = None,
        featured_cards: Optional[List[str]] = None,
        delay_before_start: float = 0,
        notify_players: bool = True
    ) -> str:
        """Create a time-limited flash banner with auto-expiration.
        
        Args:
            banner_id: Unique identifier
            name: Display name
            description: Banner description
            card_pool: List of card templates
            duration_seconds: How long banner stays active
            custom_weights: Optional custom rarity weights
            featured_cards: List of featured card IDs
            delay_before_start: Delay before activation (default: immediate)
            notify_players: Send notification when banner activates
            
        Returns:
            banner_id
            
        Example:
            >>> # Create 2-hour fire rate-up banner
            >>> manager.create_flash_banner(
            ...     banner_id="fire_rateup",
            ...     name="Fire Rate-Up!",
            ...     description="3x S-rank rate for Fire cards!",
            ...     card_pool=fire_cards,
            ...     duration_seconds=7200,
            ...     custom_weights={"S": 4.5, "SS": 1.5}
            ... )
        """
        # Create the banner
        self.create_banner(
            banner_id=banner_id,
            name=name,
            description=description,
            card_pool=card_pool,
            custom_weights=custom_weights,
            featured_cards=featured_cards
        )
        
        # Schedule activation
        scheduler = get_scheduler()
        
        async def activate_callback():
            self.activate_banner(banner_id)
            if notify_players:
                await self._fire_event("banner_activated", {
                    "banner_id": banner_id,
                    "name": name,
                    "duration_seconds": duration_seconds
                })
        
        if delay_before_start > 0:
            scheduler.schedule_once(
                callback=activate_callback,
                delay_seconds=delay_before_start,
                task_name=f"activate_banner_{banner_id}"
            )
        else:
            # Activate immediately (async)
            import asyncio
            asyncio.create_task(activate_callback())
        
        # Schedule expiration
        total_delay = delay_before_start + duration_seconds
        expiration_task_id = scheduler.schedule_once(
            callback=lambda: self.expire_banner(banner_id),
            delay_seconds=total_delay,
            task_name=f"expire_banner_{banner_id}"
        )
        
        # Store task ID for potential cancellation
        self._banners[banner_id].scheduler_task_id = expiration_task_id
        
        logger.info(
            f"Scheduled flash banner '{banner_id}' "
            f"(start: {delay_before_start}s, duration: {duration_seconds}s)"
        )
        
        return banner_id
    
    def activate_banner(self, banner_id: str) -> None:
        """Activate a banner (make it the current active banner).
        
        Args:
            banner_id: ID of banner to activate
            
        Raises:
            ValueError: If banner doesn't exist or is already expired
            
        Example:
            >>> manager.activate_banner("fire_event")
        """
        if banner_id not in self._banners:
            raise ValueError(f"Banner '{banner_id}' not found")
        
        banner = self._banners[banner_id]
        
        if banner.status == BannerStatus.EXPIRED:
            raise ValueError(f"Cannot activate expired banner '{banner_id}'")
        
        # Deactivate current banner if any
        if self._active_banner_id and self._active_banner_id != banner_id:
            old_banner = self._banners.get(self._active_banner_id)
            if old_banner and old_banner.status == BannerStatus.ACTIVE:
                old_banner.status = BannerStatus.SCHEDULED
        
        # Activate new banner
        banner.status = BannerStatus.ACTIVE
        banner.activated_at = datetime.now()
        self._active_banner_id = banner_id
        
        logger.info(f"Activated banner '{banner_id}'")
    
    def expire_banner(self, banner_id: str) -> None:
        """Expire a banner (remove from active rotation).
        
        Args:
            banner_id: ID of banner to expire
            
        Example:
            >>> manager.expire_banner("fire_event")
        """
        if banner_id not in self._banners:
            logger.warning(f"Cannot expire non-existent banner '{banner_id}'")
            return
        
        banner = self._banners[banner_id]
        banner.status = BannerStatus.EXPIRED
        banner.expired_at = datetime.now()
        
        # Fire event (only if event loop is running)
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._fire_event("banner_expired", {
                "banner_id": banner_id,
                "total_pulls": banner.total_pulls
            }))
        except RuntimeError:
            # No event loop running - skip event firing
            pass
        
        # If this was the active banner, fall back to default
        if self._active_banner_id == banner_id:
            if self._default_banner_id and self._default_banner_id != banner_id:
                # Activate default banner
                default_banner = self._banners.get(self._default_banner_id)
                if default_banner:
                    default_banner.status = BannerStatus.ACTIVE
                    if not default_banner.activated_at:
                        default_banner.activated_at = datetime.now()
                self._active_banner_id = self._default_banner_id
                logger.info(f"Expired active banner '{banner_id}', falling back to '{self._default_banner_id}'")
            else:
                self._active_banner_id = None
                logger.info(f"Expired active banner '{banner_id}', no default banner available")
        else:
            logger.info(f"Expired banner '{banner_id}'")
    
    def set_default_banner(self, banner_id: str) -> None:
        """Set the default fallback banner.
        
        This banner becomes active when flash banners expire.
        
        Args:
            banner_id: ID of banner to use as default
            
        Example:
            >>> manager.set_default_banner("standard")
        """
        if banner_id not in self._banners:
            raise ValueError(f"Banner '{banner_id}' not found")
        
        self._default_banner_id = banner_id
        
        # If no active banner, activate default
        if self._active_banner_id is None:
            self.activate_banner(banner_id)
        
        logger.info(f"Set default banner to '{banner_id}'")
    
    def get_active_banner(self) -> Optional[Dict[str, Any]]:
        """Get the currently active banner.
        
        Returns:
            Banner info dict or None if no active banner
            
        Example:
            >>> active = manager.get_active_banner()
            >>> if active:
            ...     print(f"Active: {active['name']}")
        """
        if not self._active_banner_id:
            return None
        
        banner = self._banners.get(self._active_banner_id)
        if not banner or banner.status != BannerStatus.ACTIVE:
            return None
        
        return self._banner_to_dict(banner)
    
    def get_banner_info(self, banner_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific banner.
        
        Args:
            banner_id: Banner ID
            
        Returns:
            Banner info dict or None if not found
        """
        banner = self._banners.get(banner_id)
        if not banner:
            return None
        
        return self._banner_to_dict(banner)
    
    def get_all_banners(self) -> List[Dict[str, Any]]:
        """Get information about all banners.
        
        Returns:
            List of banner info dicts
        """
        return [self._banner_to_dict(banner) for banner in self._banners.values()]
    
    def track_pull(self, banner_id: str, player_id: str, pull_count: int = 1) -> None:
        """Track gacha pulls for statistics.
        
        Args:
            banner_id: Banner where pull occurred
            player_id: ID of player who pulled
            pull_count: Number of pulls (default: 1)
        """
        if banner_id not in self._banners:
            return
        
        banner = self._banners[banner_id]
        banner.total_pulls += pull_count
        banner.unique_pullers.add(player_id)
    
    def register_event_callback(
        self,
        callback: Callable[[str, Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Register callback for banner events.
        
        Events: "banner_activated", "banner_expired"
        
        Args:
            callback: Async function(event_type, data)
            
        Example:
            >>> async def on_banner_event(event_type, data):
            ...     if event_type == "banner_activated":
            ...         await notify_all_players(data["banner_id"])
            >>> 
            >>> manager.register_event_callback(on_banner_event)
        """
        self._event_callbacks.append(callback)
    
    async def _fire_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Fire banner event to all registered callbacks."""
        for callback in self._event_callbacks:
            try:
                await callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in banner event callback: {e}", exc_info=True)
    
    def _banner_to_dict(self, banner: BannerState) -> Dict[str, Any]:
        """Convert BannerState to dictionary."""
        return {
            "banner_id": banner.config.banner_id,
            "name": banner.config.name,
            "description": banner.config.description,
            "status": banner.status.value,
            "card_pool_size": len(banner.config.card_pool),
            "custom_weights": banner.config.custom_weights,
            "featured_cards": banner.config.featured_cards,
            "pity_carries_over": banner.config.pity_carries_over,
            "total_pulls": banner.total_pulls,
            "unique_pullers": len(banner.unique_pullers),
            "created_at": banner.created_at.isoformat(),
            "activated_at": banner.activated_at.isoformat() if banner.activated_at else None,
            "expired_at": banner.expired_at.isoformat() if banner.expired_at else None
        }


# Global singleton instance
_global_banner_manager: Optional[BannerManager] = None


def get_banner_manager() -> BannerManager:
    """Get the global banner manager instance.
    
    Returns:
        Global BannerManager instance
        
    Example:
        >>> manager = get_banner_manager()
        >>> manager.create_banner(...)
    """
    global _global_banner_manager
    if _global_banner_manager is None:
        _global_banner_manager = BannerManager()
    return _global_banner_manager


def reset_banner_manager() -> None:
    """Reset the global banner manager instance.
    
    Used primarily for testing.
    """
    global _global_banner_manager
    _global_banner_manager = None

