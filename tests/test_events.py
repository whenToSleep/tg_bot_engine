"""Tests for event system.

Tests EventBus, Events, and event publishing/subscription.
"""

import pytest
from engine.core.events import (
    Event,
    EventBus,
    MobKilledEvent,
    PlayerLevelUpEvent,
    GoldChangedEvent,
    AchievementUnlockedEvent,
    ItemSpawnedEvent,
    MobSpawnedEvent,
    get_event_bus,
    reset_event_bus
)


@pytest.fixture
def event_bus():
    """Fresh event bus for each test."""
    return EventBus()


@pytest.fixture(autouse=True)
def reset_global_bus():
    """Reset global bus before each test."""
    reset_event_bus()
    yield
    reset_event_bus()


class TestEvent:
    """Tests for Event base class."""
    
    def test_event_creation(self):
        """Test creating basic event."""
        event = Event(
            event_type="test_event",
            data={"key": "value"}
        )
        
        assert event.event_type == "test_event"
        assert event.data["key"] == "value"
        assert event.timestamp is not None
    
    def test_event_default_data(self):
        """Test event with default empty data."""
        event = Event(event_type="test")
        
        assert event.data == {}


class TestSpecificEvents:
    """Tests for specific event types."""
    
    def test_mob_killed_event(self):
        """Test MobKilledEvent creation."""
        event = MobKilledEvent(
            player_id="p1",
            mob_id="m1",
            mob_template="goblin",
            damage_dealt=50
        )
        
        assert event.event_type == "mob_killed"
        assert event.data["player_id"] == "p1"
        assert event.data["mob_id"] == "m1"
        assert event.data["mob_template"] == "goblin"
        assert event.data["damage_dealt"] == 50
    
    def test_player_level_up_event(self):
        """Test PlayerLevelUpEvent creation."""
        event = PlayerLevelUpEvent(
            player_id="p1",
            old_level=5,
            new_level=6
        )
        
        assert event.event_type == "player_level_up"
        assert event.data["player_id"] == "p1"
        assert event.data["old_level"] == 5
        assert event.data["new_level"] == 6
    
    def test_gold_changed_event(self):
        """Test GoldChangedEvent creation."""
        event = GoldChangedEvent(
            player_id="p1",
            old_gold=100,
            new_gold=150,
            change=50,
            reason="quest_reward"
        )
        
        assert event.event_type == "gold_changed"
        assert event.data["player_id"] == "p1"
        assert event.data["old_gold"] == 100
        assert event.data["new_gold"] == 150
        assert event.data["change"] == 50
        assert event.data["reason"] == "quest_reward"
    
    def test_achievement_unlocked_event(self):
        """Test AchievementUnlockedEvent creation."""
        event = AchievementUnlockedEvent(
            player_id="p1",
            achievement_id="goblin_slayer",
            achievement_name="Goblin Slayer"
        )
        
        assert event.event_type == "achievement_unlocked"
        assert event.data["achievement_id"] == "goblin_slayer"
    
    def test_item_spawned_event(self):
        """Test ItemSpawnedEvent creation."""
        event = ItemSpawnedEvent(
            item_id="item_1",
            template_id="health_potion",
            quantity=5
        )
        
        assert event.event_type == "item_spawned"
        assert event.data["item_id"] == "item_1"
        assert event.data["quantity"] == 5
    
    def test_mob_spawned_event(self):
        """Test MobSpawnedEvent creation."""
        event = MobSpawnedEvent(
            mob_id="mob_1",
            template_id="goblin_warrior"
        )
        
        assert event.event_type == "mob_spawned"
        assert event.data["mob_id"] == "mob_1"


class TestEventBus:
    """Tests for EventBus pub/sub functionality."""
    
    def test_subscribe_and_publish(self, event_bus):
        """Test basic subscribe and publish."""
        received_events = []
        
        def handler(event: Event):
            received_events.append(event)
        
        event_bus.subscribe("test_event", handler)
        
        event = Event(event_type="test_event", data={"value": 42})
        event_bus.publish(event)
        
        assert len(received_events) == 1
        assert received_events[0].data["value"] == 42
    
    def test_multiple_subscribers(self, event_bus):
        """Test multiple handlers for same event."""
        call_count = [0]
        
        def handler1(event: Event):
            call_count[0] += 1
        
        def handler2(event: Event):
            call_count[0] += 10
        
        event_bus.subscribe("test_event", handler1)
        event_bus.subscribe("test_event", handler2)
        
        event = Event(event_type="test_event")
        event_bus.publish(event)
        
        assert call_count[0] == 11  # 1 + 10
    
    def test_different_event_types(self, event_bus):
        """Test handlers only receive their event types."""
        received_a = []
        received_b = []
        
        def handler_a(event: Event):
            received_a.append(event)
        
        def handler_b(event: Event):
            received_b.append(event)
        
        event_bus.subscribe("event_a", handler_a)
        event_bus.subscribe("event_b", handler_b)
        
        event_bus.publish(Event(event_type="event_a"))
        event_bus.publish(Event(event_type="event_b"))
        
        assert len(received_a) == 1
        assert len(received_b) == 1
    
    def test_unsubscribe(self, event_bus):
        """Test unsubscribing from events."""
        call_count = [0]
        
        def handler(event: Event):
            call_count[0] += 1
        
        event_bus.subscribe("test_event", handler)
        
        # Publish - should receive
        event_bus.publish(Event(event_type="test_event"))
        assert call_count[0] == 1
        
        # Unsubscribe
        event_bus.unsubscribe("test_event", handler)
        
        # Publish again - should NOT receive
        event_bus.publish(Event(event_type="test_event"))
        assert call_count[0] == 1  # Still 1
    
    def test_unsubscribe_nonexistent(self, event_bus):
        """Test unsubscribing handler that wasn't subscribed."""
        def handler(event: Event):
            pass
        
        # Should not raise error
        event_bus.unsubscribe("nonexistent", handler)
    
    def test_error_in_handler_doesnt_break_others(self, event_bus):
        """Test exception in one handler doesn't stop others."""
        call_order = []
        
        def handler1(event: Event):
            call_order.append(1)
        
        def handler2(event: Event):
            call_order.append(2)
            raise ValueError("Handler 2 error")
        
        def handler3(event: Event):
            call_order.append(3)
        
        event_bus.subscribe("test", handler1)
        event_bus.subscribe("test", handler2)
        event_bus.subscribe("test", handler3)
        
        event_bus.publish(Event(event_type="test"))
        
        # All handlers should be called despite handler2 error
        assert call_order == [1, 2, 3]
    
    def test_clear_subscribers(self, event_bus):
        """Test clearing all subscribers."""
        def handler(event: Event):
            pass
        
        event_bus.subscribe("test_a", handler)
        event_bus.subscribe("test_b", handler)
        
        assert event_bus.get_subscriber_count("test_a") == 1
        assert event_bus.get_subscriber_count("test_b") == 1
        
        # Clear all
        event_bus.clear_subscribers()
        
        assert event_bus.get_subscriber_count("test_a") == 0
        assert event_bus.get_subscriber_count("test_b") == 0
    
    def test_clear_subscribers_specific_type(self, event_bus):
        """Test clearing subscribers for specific event type."""
        def handler(event: Event):
            pass
        
        event_bus.subscribe("test_a", handler)
        event_bus.subscribe("test_b", handler)
        
        # Clear only test_a
        event_bus.clear_subscribers("test_a")
        
        assert event_bus.get_subscriber_count("test_a") == 0
        assert event_bus.get_subscriber_count("test_b") == 1
    
    def test_get_subscriber_count(self, event_bus):
        """Test getting subscriber count."""
        def handler1(event: Event):
            pass
        
        def handler2(event: Event):
            pass
        
        assert event_bus.get_subscriber_count("test") == 0
        
        event_bus.subscribe("test", handler1)
        assert event_bus.get_subscriber_count("test") == 1
        
        event_bus.subscribe("test", handler2)
        assert event_bus.get_subscriber_count("test") == 2
    
    def test_event_history(self, event_bus):
        """Test event history tracking."""
        event1 = Event(event_type="test_1")
        event2 = Event(event_type="test_2")
        
        event_bus.publish(event1)
        event_bus.publish(event2)
        
        history = event_bus.get_event_history()
        
        assert len(history) == 2
        assert history[0].event_type == "test_1"
        assert history[1].event_type == "test_2"
    
    def test_event_history_filtered(self, event_bus):
        """Test filtering event history by type."""
        event_bus.publish(Event(event_type="type_a"))
        event_bus.publish(Event(event_type="type_b"))
        event_bus.publish(Event(event_type="type_a"))
        
        history_a = event_bus.get_event_history("type_a")
        history_b = event_bus.get_event_history("type_b")
        
        assert len(history_a) == 2
        assert len(history_b) == 1
    
    def test_clear_history(self, event_bus):
        """Test clearing event history."""
        event_bus.publish(Event(event_type="test"))
        event_bus.publish(Event(event_type="test"))
        
        assert len(event_bus.get_event_history()) == 2
        
        event_bus.clear_history()
        
        assert len(event_bus.get_event_history()) == 0


class TestGlobalEventBus:
    """Tests for global event bus singleton."""
    
    def test_get_global_event_bus(self):
        """Test getting global event bus."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        
        # Should be same instance
        assert bus1 is bus2
    
    def test_reset_global_event_bus(self):
        """Test resetting global event bus."""
        bus1 = get_event_bus()
        
        # Subscribe to something
        def handler(event: Event):
            pass
        bus1.subscribe("test", handler)
        assert bus1.get_subscriber_count("test") == 1
        
        # Reset
        reset_event_bus()
        
        # Get new bus
        bus2 = get_event_bus()
        
        # Should be different instance with no subscribers
        assert bus2 is not bus1
        assert bus2.get_subscriber_count("test") == 0

