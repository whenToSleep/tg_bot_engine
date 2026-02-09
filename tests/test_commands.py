"""Unit tests for game commands.

Tests all commands to ensure 100% coverage and correct behavior.
"""

import pytest
from engine.core.state import GameState
from engine.core.executor import CommandExecutor
from engine.commands.economy import GainGoldCommand, SpendGoldCommand
from engine.commands.combat import AttackMobCommand


class TestGainGoldCommand:
    """Tests for GainGoldCommand."""
    
    def test_gain_gold_new_player(self, game_state: GameState, executor: CommandExecutor):
        """Test adding gold to a new player (creates player)."""
        cmd = GainGoldCommand("player_1", 100)
        result = executor.execute(cmd, game_state)
        
        assert result.success is True
        assert result.data["new_gold"] == 100
        assert result.error is None
        
        # Verify state was updated
        player = game_state.get_entity("player_1")
        assert player is not None
        assert player["gold"] == 100
    
    def test_gain_gold_existing_player(self, populated_state: GameState, executor: CommandExecutor):
        """Test adding gold to existing player."""
        cmd = GainGoldCommand("player_1", 50)
        result = executor.execute(cmd, populated_state)
        
        assert result.success is True
        assert result.data["new_gold"] == 150  # 100 + 50
        
        player = populated_state.get_entity("player_1")
        assert player["gold"] == 150
    
    def test_gain_gold_zero(self, game_state: GameState, executor: CommandExecutor):
        """Test adding zero gold."""
        cmd = GainGoldCommand("player_1", 0)
        result = executor.execute(cmd, game_state)
        
        assert result.success is True
        assert result.data["new_gold"] == 0


class TestSpendGoldCommand:
    """Tests for SpendGoldCommand."""
    
    def test_spend_gold_success(self, populated_state: GameState, executor: CommandExecutor):
        """Test spending gold when player has enough."""
        cmd = SpendGoldCommand("player_1", 30)
        result = executor.execute(cmd, populated_state)
        
        assert result.success is True
        assert result.data["new_gold"] == 70  # 100 - 30
        
        player = populated_state.get_entity("player_1")
        assert player["gold"] == 70
    
    def test_spend_gold_insufficient(self, populated_state: GameState, executor: CommandExecutor):
        """Test spending more gold than player has."""
        cmd = SpendGoldCommand("player_1", 150)
        result = executor.execute(cmd, populated_state)
        
        assert result.success is False
        assert result.data is None
        assert "Not enough gold" in result.error
        
        # Verify gold was NOT spent
        player = populated_state.get_entity("player_1")
        assert player["gold"] == 100  # Unchanged
    
    def test_spend_gold_exact_amount(self, populated_state: GameState, executor: CommandExecutor):
        """Test spending exactly all gold."""
        cmd = SpendGoldCommand("player_1", 100)
        result = executor.execute(cmd, populated_state)
        
        assert result.success is True
        assert result.data["new_gold"] == 0
    
    def test_spend_gold_nonexistent_player(self, game_state: GameState, executor: CommandExecutor):
        """Test spending gold for non-existent player."""
        cmd = SpendGoldCommand("player_999", 50)
        result = executor.execute(cmd, game_state)
        
        assert result.success is False
        assert "not exist" in result.error.lower()


class TestAttackMobCommand:
    """Tests for AttackMobCommand."""
    
    def test_attack_mob_damage(self, populated_state: GameState, executor: CommandExecutor):
        """Test attacking mob deals damage."""
        cmd = AttackMobCommand("player_1", "mob_1")
        result = executor.execute(cmd, populated_state)
        
        assert result.success is True
        assert result.data["damage_dealt"] == 10  # Player's attack stat
        assert result.data["mob_hp"] == 40  # 50 - 10
        assert result.data["mob_killed"] is False
        assert result.data["gold_gained"] == 0
        
        # Verify mob HP updated
        mob = populated_state.get_entity("mob_1")
        assert mob is not None
        assert mob["hp"] == 40
    
    def test_attack_mob_kill(self, populated_state: GameState, executor: CommandExecutor):
        """Test killing a mob gives reward."""
        # Set mob HP low enough to kill in one hit
        mob = populated_state.get_entity("mob_1")
        mob["hp"] = 10
        populated_state.set_entity("mob_1", mob)
        
        cmd = AttackMobCommand("player_1", "mob_1")
        result = executor.execute(cmd, populated_state)
        
        assert result.success is True
        assert result.data["damage_dealt"] == 10
        assert result.data["mob_hp"] == 0
        assert result.data["mob_killed"] is True
        assert result.data["gold_gained"] == 25  # Mob's gold_reward
        
        # Verify mob was deleted
        mob_after = populated_state.get_entity("mob_1")
        assert mob_after is None
        
        # Verify player got gold
        player = populated_state.get_entity("player_1")
        assert player["gold"] == 125  # 100 + 25
    
    def test_attack_mob_multiple_attacks(self, populated_state: GameState, executor: CommandExecutor):
        """Test multiple attacks to kill mob."""
        # Attack 5 times to kill mob (50 HP / 10 damage = 5 attacks)
        for i in range(4):
            cmd = AttackMobCommand("player_1", "mob_1")
            result = executor.execute(cmd, populated_state)
            assert result.success is True
            assert result.data["mob_killed"] is False
        
        # Fifth attack kills the mob
        cmd = AttackMobCommand("player_1", "mob_1")
        result = executor.execute(cmd, populated_state)
        
        assert result.success is True
        assert result.data["mob_killed"] is True
        assert populated_state.get_entity("mob_1") is None
    
    def test_attack_nonexistent_mob(self, game_state: GameState, executor: CommandExecutor):
        """Test attacking non-existent mob."""
        game_state.set_entity("player_1", {"attack": 10, "gold": 0})
        
        cmd = AttackMobCommand("player_1", "mob_999")
        result = executor.execute(cmd, game_state)
        
        assert result.success is False
        assert "not exist" in result.error.lower()
    
    def test_attack_with_nonexistent_player(self, game_state: GameState, executor: CommandExecutor):
        """Test attack by non-existent player."""
        game_state.set_entity("mob_1", {"hp": 50, "gold_reward": 25})
        
        cmd = AttackMobCommand("player_999", "mob_1")
        result = executor.execute(cmd, game_state)
        
        assert result.success is False
        assert "not exist" in result.error.lower()


class TestGameState:
    """Tests for GameState."""
    
    def test_set_and_get_entity(self, game_state: GameState):
        """Test setting and getting entity."""
        entity_data = {"test": "data", "value": 42}
        game_state.set_entity("test_entity", entity_data)
        
        retrieved = game_state.get_entity("test_entity")
        assert retrieved == entity_data
    
    def test_get_nonexistent_entity(self, game_state: GameState):
        """Test getting non-existent entity returns None."""
        result = game_state.get_entity("nonexistent")
        assert result is None
    
    def test_delete_entity(self, game_state: GameState):
        """Test deleting entity."""
        game_state.set_entity("test", {"data": 1})
        assert game_state.exists("test") is True
        
        game_state.delete_entity("test")
        assert game_state.exists("test") is False
    
    def test_delete_nonexistent_entity(self, game_state: GameState):
        """Test deleting non-existent entity (should not error)."""
        game_state.delete_entity("nonexistent")  # Should not raise
    
    def test_exists(self, game_state: GameState):
        """Test exists method."""
        assert game_state.exists("test") is False
        
        game_state.set_entity("test", {})
        assert game_state.exists("test") is True
    
    def test_clear(self, game_state: GameState):
        """Test clearing all entities."""
        game_state.set_entity("entity1", {"data": 1})
        game_state.set_entity("entity2", {"data": 2})
        assert game_state.entity_count() == 2
        
        game_state.clear()
        assert game_state.entity_count() == 0
        assert game_state.get_entity("entity1") is None
    
    def test_entity_count(self, game_state: GameState):
        """Test entity count."""
        assert game_state.entity_count() == 0
        
        game_state.set_entity("e1", {})
        assert game_state.entity_count() == 1
        
        game_state.set_entity("e2", {})
        assert game_state.entity_count() == 2
        
        game_state.delete_entity("e1")
        assert game_state.entity_count() == 1


class TestCommandExecutor:
    """Tests for CommandExecutor."""
    
    def test_executor_success(self, game_state: GameState, executor: CommandExecutor):
        """Test executor with successful command."""
        cmd = GainGoldCommand("player_1", 100)
        result = executor.execute(cmd, game_state)
        
        assert result.success is True
        assert result.error is None
    
    def test_executor_validation_error(self, game_state: GameState, executor: CommandExecutor):
        """Test executor with validation error."""
        game_state.set_entity("player_1", {"gold": 10})
        cmd = SpendGoldCommand("player_1", 100)
        result = executor.execute(cmd, game_state)
        
        assert result.success is False
        assert "Validation error" in result.error
    
    def test_executor_key_error(self, game_state: GameState, executor: CommandExecutor):
        """Test executor with KeyError (entity not found)."""
        cmd = SpendGoldCommand("nonexistent", 50)
        result = executor.execute(cmd, game_state)
        
        assert result.success is False
        assert "Entity not found" in result.error

