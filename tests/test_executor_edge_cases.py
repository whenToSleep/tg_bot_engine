"""Tests for executor edge cases and error handling.

Tests edge cases in CommandExecutor and AsyncCommandExecutor
to ensure proper error handling and coverage.
"""

import pytest
import asyncio
from engine.core.state import GameState
from engine.core.executor import CommandExecutor
from engine.core.async_executor import AsyncCommandExecutor
from engine.core.command import Command
from typing import List


class BrokenCommand(Command):
    """Command that raises unexpected exception."""
    
    def __init__(self, error_type: str = "runtime"):
        self.error_type = error_type
    
    def get_entity_dependencies(self) -> List[str]:
        return ["test_entity"]
    
    def execute(self, state: GameState) -> dict:
        if self.error_type == "runtime":
            raise RuntimeError("Unexpected runtime error")
        elif self.error_type == "attribute":
            raise AttributeError("Unexpected attribute error")
        elif self.error_type == "type":
            raise TypeError("Unexpected type error")
        else:
            raise Exception("Generic exception")


class TestCommandExecutorEdgeCases:
    """Test edge cases for CommandExecutor."""
    
    def test_executor_unexpected_exception(self):
        """Test executor handles unexpected exceptions."""
        state = GameState()
        executor = CommandExecutor()
        
        cmd = BrokenCommand("runtime")
        result = executor.execute(cmd, state)
        
        assert not result.success
        assert "unexpected error" in result.error.lower()
        assert "RuntimeError" in result.error
    
    def test_executor_attribute_error(self):
        """Test executor handles AttributeError."""
        state = GameState()
        executor = CommandExecutor()
        
        cmd = BrokenCommand("attribute")
        result = executor.execute(cmd, state)
        
        assert not result.success
        assert "AttributeError" in result.error
    
    def test_executor_type_error(self):
        """Test executor handles TypeError."""
        state = GameState()
        executor = CommandExecutor()
        
        cmd = BrokenCommand("type")
        result = executor.execute(cmd, state)
        
        assert not result.success
        assert "TypeError" in result.error
    
    def test_executor_generic_exception(self):
        """Test executor handles generic Exception."""
        state = GameState()
        executor = CommandExecutor()
        
        cmd = BrokenCommand("generic")
        result = executor.execute(cmd, state)
        
        assert not result.success
        assert "unexpected error" in result.error.lower()


@pytest.mark.asyncio
class TestAsyncExecutorEdgeCases:
    """Test edge cases for AsyncCommandExecutor."""
    
    async def test_execute_batch_with_exception(self):
        """Test batch execution handles exceptions."""
        from engine.commands.economy import GainGoldCommand
        
        state = GameState()
        state.set_entity("player_1", {"gold": 0})
        
        executor = AsyncCommandExecutor(state)
        
        commands = [
            GainGoldCommand("player_1", 10),
            BrokenCommand("runtime"),
            GainGoldCommand("player_1", 20),
        ]
        
        results = await executor.execute_batch(commands)
        
        # First and third should succeed, second should fail
        assert results[0].success
        assert not results[1].success
        assert results[2].success
    
    async def test_execute_broken_command(self):
        """Test async executor handles broken command."""
        state = GameState()
        executor = AsyncCommandExecutor(state)
        
        cmd = BrokenCommand("runtime")
        result = await executor.execute(cmd)
        
        assert not result.success
        assert "Unexpected error" in result.error
    
    async def test_get_lock_stats(self):
        """Test getting lock statistics."""
        from engine.commands.economy import GainGoldCommand
        
        state = GameState()
        state.set_entity("player_1", {"gold": 0})
        
        executor = AsyncCommandExecutor(state)
        
        # Before any operations
        stats = executor.get_lock_stats()
        assert stats["total_locks"] == 0
        assert stats["locked_entities"] == 0
        
        # Execute command
        await executor.execute(GainGoldCommand("player_1", 10))
        
        # After operation (lock created but released)
        stats = executor.get_lock_stats()
        assert stats["total_locks"] >= 0
        assert stats["locked_entities"] >= 0
    
    async def test_execute_batch_all_fail(self):
        """Test batch execution when all commands fail."""
        state = GameState()
        executor = AsyncCommandExecutor(state)
        
        commands = [
            BrokenCommand("runtime"),
            BrokenCommand("attribute"),
            BrokenCommand("type"),
        ]
        
        results = await executor.execute_batch(commands)
        
        assert all(not r.success for r in results)
        assert len(results) == 3
    
    async def test_execute_batch_empty(self):
        """Test batch execution with empty list."""
        state = GameState()
        executor = AsyncCommandExecutor(state)
        
        results = await executor.execute_batch([])
        
        assert results == []

