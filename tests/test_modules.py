"""Tests for game modules.

Tests AchievementModule and ProgressionModule with event integration.
"""

import pytest
from engine.core.state import GameState
from engine.core.events import (
    reset_event_bus,
    get_event_bus,
    MobKilledEvent,
    PlayerLevelUpEvent,
    AchievementUnlockedEvent,
    GoldChangedEvent
)
from engine.modules.achievements import AchievementModule
from engine.modules.progression import ProgressionModule
from engine.core.data_loader import reset_global_loader


@pytest.fixture
def game_state():
    """Fresh game state for each test."""
    return GameState()


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global singletons before each test."""
    reset_event_bus()
    reset_global_loader()
    yield
    reset_event_bus()
    reset_global_loader()


class TestAchievementModule:
    """Tests for AchievementModule."""
    
    def test_module_subscribes_to_events(self, game_state):
        """Test module subscribes to mob_killed."""
        event_bus = get_event_bus()
        module = AchievementModule(game_state)
        
        # Should have subscriber
        assert event_bus.get_subscriber_count("mob_killed") == 1
    
    def test_goblin_slayer_achievement(self, game_state):
        """Test Goblin Slayer achievement (kill 10 goblins)."""
        # Create player
        game_state.set_entity("player_1", {"gold": 0})
        
        # Create module
        module = AchievementModule(game_state)
        event_bus = get_event_bus()
        
        # Track achievement unlocks
        unlocked_achievements = []
        
        def on_achievement(event):
            unlocked_achievements.append(event.data["achievement_id"])
        
        event_bus.subscribe("achievement_unlocked", on_achievement)
        
        # Kill 9 goblins - should not unlock
        for i in range(9):
            event_bus.publish(MobKilledEvent(
                player_id="player_1",
                mob_id=f"goblin_{i}",
                mob_template="goblin_warrior"
            ))
        
        assert len(unlocked_achievements) == 0
        
        # Kill 10th goblin - should unlock
        event_bus.publish(MobKilledEvent(
            player_id="player_1",
            mob_id="goblin_10",
            mob_template="goblin_warrior"
        ))
        
        assert len(unlocked_achievements) == 1
        assert unlocked_achievements[0] == "goblin_slayer"
        
        # Check player has achievement
        player = game_state.get_entity("player_1")
        assert "goblin_slayer" in player["achievements"]
        assert player["achievements"]["goblin_slayer"]["unlocked"]
    
    def test_goblin_slayer_gold_reward(self, game_state):
        """Test Goblin Slayer grants 1000 gold."""
        game_state.set_entity("player_1", {"gold": 0})
        
        module = AchievementModule(game_state)
        event_bus = get_event_bus()
        
        # Kill 10 goblins
        for i in range(10):
            event_bus.publish(MobKilledEvent(
                player_id="player_1",
                mob_id=f"goblin_{i}",
                mob_template="goblin_warrior"
            ))
        
        # Check gold
        player = game_state.get_entity("player_1")
        assert player["gold"] == 1000
    
    def test_dragon_slayer_instant(self, game_state):
        """Test Dragon Slayer unlocks instantly."""
        game_state.set_entity("player_1", {"gold": 0})
        
        module = AchievementModule(game_state)
        event_bus = get_event_bus()
        
        unlocked = []
        event_bus.subscribe("achievement_unlocked", lambda e: unlocked.append(e.data["achievement_id"]))
        
        # Kill 1 dragon
        event_bus.publish(MobKilledEvent(
            player_id="player_1",
            mob_id="dragon_1",
            mob_template="dragon_ancient"
        ))
        
        assert "dragon_slayer" in unlocked
        
        player = game_state.get_entity("player_1")
        assert player["gold"] == 10000  # Dragon slayer reward
    
    def test_monster_hunter_achievement(self, game_state):
        """Test Monster Hunter (50 kills total)."""
        game_state.set_entity("player_1", {"gold": 0})
        
        module = AchievementModule(game_state)
        event_bus = get_event_bus()
        
        unlocked = []
        event_bus.subscribe("achievement_unlocked", lambda e: unlocked.append(e.data["achievement_id"]))
        
        # Kill 50 different monsters
        for i in range(50):
            event_bus.publish(MobKilledEvent(
                player_id="player_1",
                mob_id=f"mob_{i}",
                mob_template="goblin_warrior"  # Any mob type
            ))
        
        assert "monster_hunter" in unlocked
    
    def test_multiple_achievements(self, game_state):
        """Test unlocking multiple achievements."""
        game_state.set_entity("player_1", {"gold": 0})
        
        module = AchievementModule(game_state)
        event_bus = get_event_bus()
        
        unlocked = []
        event_bus.subscribe("achievement_unlocked", lambda e: unlocked.append(e.data["achievement_id"]))
        
        # Kill 10 goblins (goblin_slayer)
        for i in range(10):
            event_bus.publish(MobKilledEvent(
                player_id="player_1",
                mob_id=f"goblin_{i}",
                mob_template="goblin_warrior"
            ))
        
        # Kill 5 orcs (orc_hunter)
        for i in range(5):
            event_bus.publish(MobKilledEvent(
                player_id="player_1",
                mob_id=f"orc_{i}",
                mob_template="orc_chieftain"
            ))
        
        # Kill 1 dragon (dragon_slayer)
        event_bus.publish(MobKilledEvent(
            player_id="player_1",
            mob_id="dragon_1",
            mob_template="dragon_ancient"
        ))
        
        # Should have unlocked multiple
        assert "goblin_slayer" in unlocked
        assert "orc_hunter" in unlocked
        assert "dragon_slayer" in unlocked
    
    def test_achievement_not_unlocked_twice(self, game_state):
        """Test achievement only unlocks once."""
        game_state.set_entity("player_1", {"gold": 0})
        
        module = AchievementModule(game_state)
        event_bus = get_event_bus()
        
        unlock_count = [0]
        event_bus.subscribe("achievement_unlocked", lambda e: unlock_count.__setitem__(0, unlock_count[0] + 1))
        
        # Kill 20 goblins (double the requirement)
        for i in range(20):
            event_bus.publish(MobKilledEvent(
                player_id="player_1",
                mob_id=f"goblin_{i}",
                mob_template="goblin_warrior"
            ))
        
        # Should only unlock goblin_slayer once (monster_hunter needs 50 kills)
        assert unlock_count[0] == 1  # Only goblin_slayer unlocked


class TestProgressionModule:
    """Tests for ProgressionModule."""
    
    def test_module_subscribes_to_events(self, game_state):
        """Test module subscribes to mob_killed."""
        event_bus = get_event_bus()
        module = ProgressionModule(game_state)
        
        assert event_bus.get_subscriber_count("mob_killed") == 1
    
    def test_grants_exp_on_mob_kill(self, game_state):
        """Test exp is granted when mob is killed."""
        game_state.set_entity("player_1", {"level": 1, "exp": 0})
        
        module = ProgressionModule(game_state)
        event_bus = get_event_bus()
        
        # Kill goblin (15 exp)
        event_bus.publish(MobKilledEvent(
            player_id="player_1",
            mob_id="goblin_1",
            mob_template="goblin_warrior"
        ))
        
        player = game_state.get_entity("player_1")
        assert player["exp"] == 15
    
    def test_levelup_on_enough_exp(self, game_state):
        """Test player levels up with enough exp."""
        game_state.set_entity("player_1", {"level": 1, "exp": 0})
        
        module = ProgressionModule(game_state)
        event_bus = get_event_bus()
        
        levelup_events = []
        event_bus.subscribe("player_level_up", lambda e: levelup_events.append(e))
        
        # Level 1->2 needs 100 exp
        # Kill goblins (15 exp each) = 7 kills = 105 exp
        for i in range(7):
            event_bus.publish(MobKilledEvent(
                player_id="player_1",
                mob_id=f"goblin_{i}",
                mob_template="goblin_warrior"
            ))
        
        # Should have leveled up
        player = game_state.get_entity("player_1")
        assert player["level"] == 2
        assert player["exp"] == 5  # 105 - 100 = 5 leftover
        
        # Should have published levelup event
        assert len(levelup_events) == 1
        assert levelup_events[0].data["old_level"] == 1
        assert levelup_events[0].data["new_level"] == 2
    
    def test_stat_increases_on_levelup(self, game_state):
        """Test stats increase on levelup."""
        game_state.set_entity("player_1", {
            "level": 1,
            "exp": 0,
            "max_hp": 100,
            "hp": 100,
            "attack": 10,
            "defense": 0
        })
        
        module = ProgressionModule(game_state)
        event_bus = get_event_bus()
        
        # Gain enough exp to levelup
        for i in range(7):
            event_bus.publish(MobKilledEvent(
                player_id="player_1",
                mob_id=f"goblin_{i}",
                mob_template="goblin_warrior"
            ))
        
        player = game_state.get_entity("player_1")
        assert player["level"] == 2
        assert player["max_hp"] == 110  # +10
        assert player["hp"] == 110  # Full heal
        assert player["attack"] == 12  # +2
        assert player["defense"] == 1  # +1
    
    def test_multiple_levelups(self, game_state):
        """Test multiple levels in one exp gain."""
        game_state.set_entity("player_1", {"level": 1, "exp": 0})
        
        module = ProgressionModule(game_state)
        event_bus = get_event_bus()
        
        levelup_count = [0]
        event_bus.subscribe("player_level_up", lambda e: levelup_count.__setitem__(0, levelup_count[0] + 1))
        
        # Kill dragon (5000 exp) - should level up multiple times
        event_bus.publish(MobKilledEvent(
            player_id="player_1",
            mob_id="dragon_1",
            mob_template="dragon_ancient"
        ))
        
        player = game_state.get_entity("player_1")
        # Level 1->2: 100, 2->3: 200, 3->4: 300, ... up to level 10
        assert player["level"] >= 10
        assert levelup_count[0] >= 9
    
    def test_default_exp_for_unknown_mob(self, game_state):
        """Test default exp for unknown mob template."""
        game_state.set_entity("player_1", {"level": 1, "exp": 0})
        
        module = ProgressionModule(game_state)
        event_bus = get_event_bus()
        
        # Kill unknown mob
        event_bus.publish(MobKilledEvent(
            player_id="player_1",
            mob_id="unknown_1",
            mob_template="unknown_mob_type"
        ))
        
        player = game_state.get_entity("player_1")
        assert player["exp"] == 10  # Default exp


class TestModuleIntegration:
    """Integration tests for multiple modules working together."""
    
    def test_both_modules_work_together(self, game_state):
        """Test Achievement + Progression modules together."""
        game_state.set_entity("player_1", {"gold": 0, "level": 1, "exp": 0})
        
        # Create both modules
        achievement_module = AchievementModule(game_state)
        progression_module = ProgressionModule(game_state)
        
        event_bus = get_event_bus()
        
        # Track events
        levelups = []
        achievements = []
        event_bus.subscribe("player_level_up", lambda e: levelups.append(e))
        event_bus.subscribe("achievement_unlocked", lambda e: achievements.append(e))
        
        # Kill 10 goblins
        for i in range(10):
            event_bus.publish(MobKilledEvent(
                player_id="player_1",
                mob_id=f"goblin_{i}",
                mob_template="goblin_warrior"
            ))
        
        player = game_state.get_entity("player_1")
        
        # Should have leveled up (10 * 15 exp = 150 exp)
        assert player["level"] == 2
        assert len(levelups) == 1
        
        # Should have unlocked goblin_slayer
        assert len(achievements) == 1
        assert achievements[0].data["achievement_id"] == "goblin_slayer"
        
        # Should have gold from achievement
        assert player["gold"] == 1000
    
    def test_events_dont_interfere(self, game_state):
        """Test event handlers don't interfere with each other."""
        game_state.set_entity("player_1", {"gold": 0, "level": 1, "exp": 0})
        
        achievement_module = AchievementModule(game_state)
        progression_module = ProgressionModule(game_state)
        
        event_bus = get_event_bus()
        
        # Both modules should handle the same event
        event_bus.publish(MobKilledEvent(
            player_id="player_1",
            mob_id="goblin_1",
            mob_template="goblin_warrior"
        ))
        
        player = game_state.get_entity("player_1")
        
        # Progression should have granted exp
        assert player["exp"] == 15
        
        # Achievement should have tracked progress
        assert "achievement_progress" in player
        assert player["achievement_progress"].get("goblin_slayer", 0) == 1

