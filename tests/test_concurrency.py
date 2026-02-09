"""Tests for concurrent command execution.

Tests the AsyncCommandExecutor and entity locking to ensure
no race conditions and proper deadlock prevention.
"""

import pytest
import asyncio
from engine.core.state import GameState
from engine.core.async_executor import AsyncCommandExecutor
from engine.commands.economy import GainGoldCommand, SpendGoldCommand
from engine.commands.combat import AttackMobCommand


@pytest.mark.asyncio
class TestConcurrentExecution:
    """Tests for concurrent command execution."""
    
    async def test_concurrent_gold_gain(self):
        """Test 100 parallel GainGold commands don't lose changes."""
        state = GameState()
        state.set_entity("player_1", {"gold": 0})
        
        executor = AsyncCommandExecutor(state)
        
        # Create 100 commands to add 10 gold each
        commands = [GainGoldCommand("player_1", 10) for _ in range(100)]
        
        # Execute in parallel
        results = await asyncio.gather(*[
            executor.execute(cmd) for cmd in commands
        ])
        
        # All should succeed
        assert all(r.success for r in results)
        
        # Gold should be exactly 1000 (no lost updates)
        assert state.get_entity("player_1")["gold"] == 1000
    
    async def test_concurrent_attack_same_mob(self):
        """Test two players attacking same mob doesn't cause race condition."""
        state = GameState()
        state.set_entity("player_1", {"attack": 10, "gold": 0})
        state.set_entity("player_2", {"attack": 15, "gold": 0})
        state.set_entity("mob_1", {"hp": 20, "gold_reward": 100})
        
        executor = AsyncCommandExecutor(state)
        
        # Both players attack simultaneously
        cmd1 = AttackMobCommand("player_1", "mob_1")
        cmd2 = AttackMobCommand("player_2", "mob_1")
        
        results = await asyncio.gather(
            executor.execute(cmd1),
            executor.execute(cmd2)
        )
        
        # Both should succeed
        assert all(r.success for r in results)
        
        # Mob should be killed (10 + 15 = 25 damage >= 20 HP)
        mob = state.get_entity("mob_1")
        assert mob is None  # Mob deleted after death
        
        # Total gold should be exactly 100 (no duplication)
        total_gold = (
            state.get_entity("player_1")["gold"] +
            state.get_entity("player_2")["gold"]
        )
        assert total_gold == 100
    
    async def test_concurrent_spend_insufficient(self):
        """Test concurrent spend with insufficient gold."""
        state = GameState()
        state.set_entity("player_1", {"gold": 100})
        
        executor = AsyncCommandExecutor(state)
        
        # Try to spend 60 gold twice simultaneously (total 120 > 100)
        commands = [SpendGoldCommand("player_1", 60) for _ in range(2)]
        
        results = await asyncio.gather(*[
            executor.execute(cmd) for cmd in commands
        ])
        
        # Exactly one should succeed, one should fail
        success_count = sum(1 for r in results if r.success)
        fail_count = sum(1 for r in results if not r.success)
        
        assert success_count == 1
        assert fail_count == 1
        
        # Gold should be 40 (100 - 60)
        assert state.get_entity("player_1")["gold"] == 40
    
    async def test_no_race_in_complex_scenario(self):
        """Test complex scenario with multiple operations."""
        state = GameState()
        state.set_entity("player_1", {"gold": 100, "attack": 10})
        state.set_entity("mob_1", {"hp": 50, "gold_reward": 50})
        
        executor = AsyncCommandExecutor(state)
        
        # Mix of operations
        commands = [
            GainGoldCommand("player_1", 20),
            SpendGoldCommand("player_1", 10),
            AttackMobCommand("player_1", "mob_1"),
            GainGoldCommand("player_1", 30),
        ]
        
        results = await asyncio.gather(*[
            executor.execute(cmd) for cmd in commands
        ])
        
        # Most should succeed
        success_count = sum(1 for r in results if r.success)
        assert success_count >= 3
        
        # Final state should be consistent
        player = state.get_entity("player_1")
        assert player is not None
        assert player["gold"] >= 100  # Should have gained gold


@pytest.mark.asyncio
class TestDeadlockPrevention:
    """Tests for deadlock prevention."""
    
    async def test_cross_entity_no_deadlock(self):
        """Test cross-entity operations don't cause deadlock."""
        state = GameState()
        state.set_entity("player_1", {"gold": 100, "attack": 10})
        state.set_entity("player_2", {"gold": 100, "attack": 10})
        state.set_entity("mob_1", {"hp": 50, "gold_reward": 25})
        state.set_entity("mob_2", {"hp": 50, "gold_reward": 25})
        
        executor = AsyncCommandExecutor(state)
        
        # Cross-attacks that could deadlock if not sorted
        commands = [
            AttackMobCommand("player_1", "mob_1"),
            AttackMobCommand("player_2", "mob_2"),
            AttackMobCommand("player_1", "mob_2"),
            AttackMobCommand("player_2", "mob_1"),
        ]
        
        # Should complete without timeout (no deadlock)
        results = await asyncio.wait_for(
            asyncio.gather(*[executor.execute(cmd) for cmd in commands]),
            timeout=5.0
        )
        
        assert all(r.success for r in results)
    
    async def test_sorted_locking_order(self):
        """Test entity locking uses sorted order."""
        state = GameState()
        state.set_entity("player_1", {"gold": 0, "attack": 10})
        state.set_entity("mob_1", {"hp": 100, "gold_reward": 50})
        
        executor = AsyncCommandExecutor(state)
        
        # Attack command should lock entities in sorted order
        cmd = AttackMobCommand("player_1", "mob_1")
        
        # Get dependencies - should be sorted
        deps = cmd.get_entity_dependencies()
        assert deps == sorted(deps)
        
        # Execute should not deadlock
        result = await asyncio.wait_for(
            executor.execute(cmd),
            timeout=1.0
        )
        
        assert result.success


@pytest.mark.asyncio
class TestStressTests:
    """Stress tests for concurrent execution."""
    
    async def test_1000_concurrent_commands(self):
        """Stress test with 1000 concurrent commands."""
        state = GameState()
        state.set_entity("player_1", {"gold": 0})
        
        executor = AsyncCommandExecutor(state)
        
        # 1000 commands adding 1 gold each
        commands = [GainGoldCommand("player_1", 1) for _ in range(1000)]
        
        results = await asyncio.gather(*[
            executor.execute(cmd) for cmd in commands
        ])
        
        # All should succeed
        assert all(r.success for r in results)
        
        # Verify no lost updates
        assert state.get_entity("player_1")["gold"] == 1000
    
    async def test_batch_execution(self):
        """Test batch command execution."""
        state = GameState()
        state.set_entity("player_1", {"gold": 0})
        
        executor = AsyncCommandExecutor(state)
        
        commands = [GainGoldCommand("player_1", 5) for _ in range(20)]
        
        # Execute as batch
        results = await executor.execute_batch(commands)
        
        assert all(r.success for r in results)
        assert state.get_entity("player_1")["gold"] == 100
    
    async def test_lock_stats(self):
        """Test lock statistics."""
        state = GameState()
        executor = AsyncCommandExecutor(state)
        
        stats = executor.get_lock_stats()
        
        assert "total_locks" in stats
        assert "locked_entities" in stats
        assert stats["total_locks"] >= 0
        assert stats["locked_entities"] >= 0

