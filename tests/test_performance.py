"""Performance benchmark tests.

Tests to ensure commands execute with acceptable performance.
Target: 1000 commands should complete in < 100ms
"""

import time
import pytest
from engine.core.state import GameState
from engine.core.executor import CommandExecutor
from engine.commands.economy import GainGoldCommand, SpendGoldCommand
from engine.commands.combat import AttackMobCommand


@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmark tests."""
    
    def test_1000_commands_under_100ms(self):
        """Test that 1000 commands execute in under 100ms.
        
        This is the key performance requirement for Iteration 0.
        """
        state = GameState()
        executor = CommandExecutor()
        
        # Setup: Create player
        state.set_entity("player_1", {"gold": 0, "attack": 10})
        
        # Prepare 1000 commands
        commands = []
        for i in range(1000):
            if i % 3 == 0:
                commands.append(GainGoldCommand("player_1", 10))
            elif i % 3 == 1:
                commands.append(SpendGoldCommand("player_1", 5))
            else:
                # Create mob for attack
                mob_id = f"mob_{i}"
                state.set_entity(mob_id, {"hp": 100, "gold_reward": 5})
                commands.append(AttackMobCommand("player_1", mob_id))
        
        # Execute and measure time
        start_time = time.perf_counter()
        
        for cmd in commands:
            result = executor.execute(cmd, state)
            # We don't care if some fail (e.g., insufficient gold)
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        print(f"\n1000 commands executed in {duration_ms:.2f}ms")
        print(f"Average per command: {duration_ms/1000:.4f}ms")
        
        # Assert performance requirement
        assert duration_ms < 100, f"Too slow: {duration_ms:.2f}ms (target: < 100ms)"
    
    def test_single_command_performance(self):
        """Test single command execution time.
        
        Target: < 0.1ms per command
        """
        state = GameState()
        executor = CommandExecutor()
        state.set_entity("player_1", {"gold": 0})
        
        # Measure 100 commands and get average
        cmd = GainGoldCommand("player_1", 1)
        
        start_time = time.perf_counter()
        for _ in range(100):
            executor.execute(cmd, state)
        end_time = time.perf_counter()
        
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        print(f"\nAverage command time: {avg_time_ms:.4f}ms")
        
        # Target: < 0.1ms
        assert avg_time_ms < 0.1, f"Too slow: {avg_time_ms:.4f}ms (target: < 0.1ms)"
    
    def test_state_operations_performance(self):
        """Test GameState operations performance."""
        state = GameState()
        
        # Test 10000 set/get operations
        start_time = time.perf_counter()
        
        for i in range(10000):
            entity_id = f"entity_{i % 100}"  # Reuse 100 entity IDs
            state.set_entity(entity_id, {"value": i})
            _ = state.get_entity(entity_id)
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        print(f"\n10000 state operations in {duration_ms:.2f}ms")
        print(f"Average per operation: {duration_ms/10000:.4f}ms")
        
        # Should be very fast (< 100ms for 10k operations)
        assert duration_ms < 100, f"State operations too slow: {duration_ms:.2f}ms"
    
    def test_complex_command_sequence(self):
        """Test realistic game sequence performance."""
        state = GameState()
        executor = CommandExecutor()
        
        # Setup player
        state.set_entity("player_1", {"gold": 1000, "attack": 10})
        
        # Simulate 100 game rounds (gain gold, spend gold, attack mob)
        start_time = time.perf_counter()
        
        for i in range(100):
            # Round: gain gold -> spend gold -> attack mob -> gain gold from kill
            executor.execute(GainGoldCommand("player_1", 20), state)
            executor.execute(SpendGoldCommand("player_1", 10), state)
            
            mob_id = f"mob_{i}"
            state.set_entity(mob_id, {"hp": 10, "gold_reward": 15})
            executor.execute(AttackMobCommand("player_1", mob_id), state)
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        print(f"\n100 game rounds in {duration_ms:.2f}ms")
        
        # 100 rounds * 3 commands = 300 commands should be < 30ms
        assert duration_ms < 30, f"Game sequence too slow: {duration_ms:.2f}ms"

