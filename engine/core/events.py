"""Events module - Event-driven architecture for game engine.

Provides event bus for decoupled, reactive game modules.
Modules can publish and subscribe to events without knowing about each other.
"""

from datetime import datetime
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Event:
    """Base event class.
    
    All game events inherit from this class.
    Events are immutable records of what happened in the game.
    
    Attributes:
        event_type: Type identifier for this event
        timestamp: When the event occurred
        data: Event-specific data payload
        
    Example:
        >>> event = Event(
        ...     event_type="player_joined",
        ...     data={"player_id": "player_1"}
        ... )
    """
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MobKilledEvent(Event):
    """Event fired when a mob is killed.
    
    Example:
        >>> event = MobKilledEvent(
        ...     player_id="player_1",
        ...     mob_id="goblin_1",
        ...     mob_template="goblin_warrior"
        ... )
    """
    def __init__(
        self,
        player_id: str,
        mob_id: str,
        mob_template: str,
        damage_dealt: int = 0,
        **kwargs
    ):
        super().__init__(
            event_type="mob_killed",
            data={
                "player_id": player_id,
                "mob_id": mob_id,
                "mob_template": mob_template,
                "damage_dealt": damage_dealt,
                **kwargs
            }
        )


@dataclass
class PlayerLevelUpEvent(Event):
    """Event fired when a player levels up.
    
    Example:
        >>> event = PlayerLevelUpEvent(
        ...     player_id="player_1",
        ...     old_level=5,
        ...     new_level=6
        ... )
    """
    def __init__(
        self,
        player_id: str,
        old_level: int,
        new_level: int,
        **kwargs
    ):
        super().__init__(
            event_type="player_level_up",
            data={
                "player_id": player_id,
                "old_level": old_level,
                "new_level": new_level,
                **kwargs
            }
        )


@dataclass
class GoldChangedEvent(Event):
    """Event fired when player's gold changes.
    
    Example:
        >>> event = GoldChangedEvent(
        ...     player_id="player_1",
        ...     old_gold=100,
        ...     new_gold=150,
        ...     change=50
        ... )
    """
    def __init__(
        self,
        player_id: str,
        old_gold: int,
        new_gold: int,
        change: int,
        reason: str = "unknown",
        **kwargs
    ):
        super().__init__(
            event_type="gold_changed",
            data={
                "player_id": player_id,
                "old_gold": old_gold,
                "new_gold": new_gold,
                "change": change,
                "reason": reason,
                **kwargs
            }
        )


@dataclass
class AchievementUnlockedEvent(Event):
    """Event fired when player unlocks achievement.
    
    Example:
        >>> event = AchievementUnlockedEvent(
        ...     player_id="player_1",
        ...     achievement_id="goblin_slayer",
        ...     achievement_name="Goblin Slayer"
        ... )
    """
    def __init__(
        self,
        player_id: str,
        achievement_id: str,
        achievement_name: str = "",
        **kwargs
    ):
        super().__init__(
            event_type="achievement_unlocked",
            data={
                "player_id": player_id,
                "achievement_id": achievement_id,
                "achievement_name": achievement_name,
                **kwargs
            }
        )


@dataclass
class ItemSpawnedEvent(Event):
    """Event fired when an item is spawned.
    
    Example:
        >>> event = ItemSpawnedEvent(
        ...     item_id="item_1",
        ...     template_id="rusty_sword",
        ...     quantity=1
        ... )
    """
    def __init__(
        self,
        item_id: str,
        template_id: str,
        quantity: int = 1,
        **kwargs
    ):
        super().__init__(
            event_type="item_spawned",
            data={
                "item_id": item_id,
                "template_id": template_id,
                "quantity": quantity,
                **kwargs
            }
        )


@dataclass
class MobSpawnedEvent(Event):
    """Event fired when a mob is spawned.
    
    Example:
        >>> event = MobSpawnedEvent(
        ...     mob_id="goblin_1",
        ...     template_id="goblin_warrior"
        ... )
    """
    def __init__(
        self,
        mob_id: str,
        template_id: str,
        **kwargs
    ):
        super().__init__(
            event_type="mob_spawned",
            data={
                "mob_id": mob_id,
                "template_id": template_id,
                **kwargs
            }
        )


class EventBus:
    """Event bus for pub/sub messaging.
    
    Allows modules to communicate without direct dependencies.
    Handlers are called synchronously in subscription order.
    
    Example:
        >>> bus = EventBus()
        >>> 
        >>> def on_mob_killed(event: Event):
        ...     print(f"Mob killed: {event.data['mob_id']}")
        >>> 
        >>> bus.subscribe("mob_killed", on_mob_killed)
        >>> bus.publish(MobKilledEvent("p1", "m1", "goblin"))
        Mob killed: m1
    """
    
    def __init__(self) -> None:
        """Initialize empty event bus."""
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._event_history: List[Event] = []
        self._max_history = 100  # Keep last 100 events
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None]
    ) -> None:
        """Subscribe handler to event type.
        
        Args:
            event_type: Type of event to listen for
            handler: Callback function(event) -> None
            
        Note:
            Same handler can be subscribed multiple times (will be called multiple times)
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None]
    ) -> None:
        """Unsubscribe handler from event type.
        
        Args:
            event_type: Type of event
            handler: Handler to remove
            
        Note:
            Does nothing if handler not subscribed (idempotent)
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not in list - ignore
    
    def publish(self, event: Event) -> None:
        """Publish event to all subscribers.
        
        Args:
            event: Event to publish
            
        Note:
            - Handlers called synchronously in subscription order
            - Exception in one handler doesn't stop other handlers
            - Exceptions are logged but not re-raised
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Get subscribers for this event type
        handlers = self._subscribers.get(event.event_type, [])
        
        # Call each handler
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but continue with other handlers
                print(f"Error in event handler for {event.event_type}: {type(e).__name__}: {e}")
    
    def clear_subscribers(self, event_type: Optional[str] = None) -> None:
        """Clear all subscribers.
        
        Args:
            event_type: If provided, only clear subscribers for this type
                       If None, clear all subscribers
        """
        if event_type is None:
            self._subscribers.clear()
        elif event_type in self._subscribers:
            self._subscribers[event_type].clear()
    
    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for event type.
        
        Args:
            event_type: Event type to check
            
        Returns:
            Number of subscribed handlers
        """
        return len(self._subscribers.get(event_type, []))
    
    def get_event_history(self, event_type: Optional[str] = None) -> List[Event]:
        """Get recent event history.
        
        Args:
            event_type: If provided, filter by event type
            
        Returns:
            List of recent events (up to max_history)
        """
        if event_type is None:
            return self._event_history.copy()
        else:
            return [e for e in self._event_history if e.event_type == event_type]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()


# Global event bus singleton
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global event bus instance.
    
    Returns:
        Global EventBus singleton
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def reset_event_bus() -> None:
    """Reset global event bus (useful for testing)."""
    global _global_event_bus
    _global_event_bus = None


# Create global event bus instance for convenient access
event_bus = get_event_bus()
