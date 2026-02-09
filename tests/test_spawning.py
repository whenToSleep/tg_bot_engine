"""Tests for spawning commands.

Tests SpawnMobCommand and SpawnItemCommand with DataLoader integration.
"""

import pytest
from engine.core.state import GameState
from engine.core.executor import CommandExecutor
from engine.core.data_loader import reset_global_loader, get_global_loader
from engine.commands.spawning import SpawnMobCommand, SpawnItemCommand


@pytest.fixture
def game_state():
    """Fresh game state for each test."""
    return GameState()


@pytest.fixture
def executor():
    """Command executor for tests."""
    return CommandExecutor()


@pytest.fixture(autouse=True)
def reset_loader():
    """Reset global loader before each test."""
    reset_global_loader()
    yield
    reset_global_loader()


class TestSpawnMobCommand:
    """Tests for SpawnMobCommand."""
    
    def test_spawn_mob_success(self, game_state, executor):
        """Test spawning mob from template."""
        cmd = SpawnMobCommand("goblin_warrior", "mob_1")
        result = executor.execute(cmd, game_state)
        
        assert result.success
        assert result.data["spawned_id"] == "mob_1"
        assert result.data["template_id"] == "goblin_warrior"
        assert result.data["name"] == "Goblin Warrior"
        assert result.data["hp"] == 50
        assert result.data["attack"] == 8
        
        # Check entity in state
        mob = game_state.get_entity("mob_1")
        assert mob is not None
        assert mob["_type"] == "mob"
        assert mob["_template_id"] == "goblin_warrior"
        assert mob["current_hp"] == 50
    
    def test_spawn_mob_template_not_found(self, game_state, executor):
        """Test spawning nonexistent mob template."""
        cmd = SpawnMobCommand("nonexistent_mob", "mob_1")
        result = executor.execute(cmd, game_state)
        
        assert not result.success
        assert "not found" in result.error.lower()
    
    def test_spawn_mob_duplicate_instance_id(self, game_state, executor):
        """Test spawning mob with existing instance ID."""
        # First spawn
        cmd1 = SpawnMobCommand("goblin_warrior", "mob_1")
        result1 = executor.execute(cmd1, game_state)
        assert result1.success
        
        # Try to spawn with same ID
        cmd2 = SpawnMobCommand("orc_chieftain", "mob_1")
        result2 = executor.execute(cmd2, game_state)
        
        assert not result2.success
        assert "already exists" in result2.error.lower()
    
    def test_spawn_multiple_mobs(self, game_state, executor):
        """Test spawning multiple mobs."""
        cmd1 = SpawnMobCommand("goblin_warrior", "mob_1")
        cmd2 = SpawnMobCommand("goblin_warrior", "mob_2")
        cmd3 = SpawnMobCommand("orc_chieftain", "mob_3")
        
        result1 = executor.execute(cmd1, game_state)
        result2 = executor.execute(cmd2, game_state)
        result3 = executor.execute(cmd3, game_state)
        
        assert all([result1.success, result2.success, result3.success])
        assert game_state.entity_count() == 3
    
    def test_spawn_mob_with_abilities(self, game_state, executor):
        """Test spawning mob with abilities."""
        cmd = SpawnMobCommand("orc_chieftain", "boss_1")
        result = executor.execute(cmd, game_state)
        
        assert result.success
        
        mob = game_state.get_entity("boss_1")
        assert "abilities" in mob
        assert len(mob["abilities"]) > 0
        assert "abilities_cooldowns" in mob
    
    def test_spawn_mob_entity_dependencies(self):
        """Test entity dependencies."""
        cmd = SpawnMobCommand("goblin_warrior", "mob_1")
        deps = cmd.get_entity_dependencies()
        
        assert deps == ["mob_1"]


class TestSpawnItemCommand:
    """Tests for SpawnItemCommand."""
    
    def test_spawn_item_success(self, game_state, executor):
        """Test spawning item from template."""
        cmd = SpawnItemCommand("rusty_sword", "item_1", quantity=1)
        result = executor.execute(cmd, game_state)
        
        assert result.success
        assert result.data["spawned_id"] == "item_1"
        assert result.data["template_id"] == "rusty_sword"
        assert result.data["name"] == "Rusty Sword"
        assert result.data["quantity"] == 1
        assert result.data["type"] == "weapon"
        
        # Check entity in state
        item = game_state.get_entity("item_1")
        assert item is not None
        assert item["_type"] == "item"
        assert item["_template_id"] == "rusty_sword"
        assert item["quantity"] == 1
    
    def test_spawn_item_stackable(self, game_state, executor):
        """Test spawning stackable item with quantity."""
        cmd = SpawnItemCommand("health_potion_small", "potion_1", quantity=10)
        result = executor.execute(cmd, game_state)
        
        assert result.success
        assert result.data["quantity"] == 10
        
        item = game_state.get_entity("potion_1")
        assert item["quantity"] == 10
        assert item["stackable"] is True
    
    def test_spawn_item_template_not_found(self, game_state, executor):
        """Test spawning nonexistent item template."""
        cmd = SpawnItemCommand("nonexistent_item", "item_1")
        result = executor.execute(cmd, game_state)
        
        assert not result.success
        assert "not found" in result.error.lower()
    
    def test_spawn_item_duplicate_instance_id(self, game_state, executor):
        """Test spawning item with existing instance ID."""
        cmd1 = SpawnItemCommand("rusty_sword", "item_1")
        result1 = executor.execute(cmd1, game_state)
        assert result1.success
        
        cmd2 = SpawnItemCommand("health_potion_small", "item_1")
        result2 = executor.execute(cmd2, game_state)
        
        assert not result2.success
        assert "already exists" in result2.error.lower()
    
    def test_spawn_item_invalid_quantity(self):
        """Test creating spawn command with invalid quantity."""
        with pytest.raises(ValueError, match="Quantity must be at least 1"):
            SpawnItemCommand("rusty_sword", "item_1", quantity=0)
    
    def test_spawn_item_non_stackable_multiple(self, game_state, executor):
        """Test spawning multiple of non-stackable item."""
        cmd = SpawnItemCommand("rusty_sword", "item_1", quantity=5)
        result = executor.execute(cmd, game_state)
        
        assert not result.success
        assert "not stackable" in result.error.lower()
    
    def test_spawn_item_exceeds_max_stack(self, game_state, executor):
        """Test spawning quantity exceeding max stack."""
        # health_potion_small has max_stack of 99
        cmd = SpawnItemCommand("health_potion_small", "potion_1", quantity=999)
        result = executor.execute(cmd, game_state)
        
        # Should fail because 999 > 99
        assert not result.success
        assert "exceeds max stack" in result.error.lower()
    
    def test_spawn_item_entity_dependencies(self):
        """Test entity dependencies."""
        cmd = SpawnItemCommand("rusty_sword", "item_1")
        deps = cmd.get_entity_dependencies()
        
        assert deps == ["item_1"]
    
    def test_spawn_multiple_items(self, game_state, executor):
        """Test spawning multiple different items."""
        cmd1 = SpawnItemCommand("rusty_sword", "item_1")
        cmd2 = SpawnItemCommand("health_potion_small", "item_2", quantity=5)
        cmd3 = SpawnItemCommand("legendary_sword", "item_3")
        
        result1 = executor.execute(cmd1, game_state)
        result2 = executor.execute(cmd2, game_state)
        result3 = executor.execute(cmd3, game_state)
        
        assert all([result1.success, result2.success, result3.success])
        assert game_state.entity_count() == 3


class TestSpawningIntegration:
    """Integration tests for spawning."""
    
    def test_spawn_mob_and_items(self, game_state, executor):
        """Test spawning both mobs and items."""
        # Spawn mob
        mob_cmd = SpawnMobCommand("goblin_warrior", "mob_1")
        mob_result = executor.execute(mob_cmd, game_state)
        
        # Spawn items from loot table
        sword_cmd = SpawnItemCommand("rusty_sword", "loot_1")
        potion_cmd = SpawnItemCommand("health_potion_small", "loot_2", quantity=2)
        
        sword_result = executor.execute(sword_cmd, game_state)
        potion_result = executor.execute(potion_cmd, game_state)
        
        assert all([mob_result.success, sword_result.success, potion_result.success])
        assert game_state.entity_count() == 3
        
        # Verify entities
        mob = game_state.get_entity("mob_1")
        sword = game_state.get_entity("loot_1")
        potions = game_state.get_entity("loot_2")
        
        assert mob["_type"] == "mob"
        assert sword["_type"] == "item"
        assert potions["_type"] == "item"
        assert potions["quantity"] == 2

