"""Tests for transaction functionality.

Tests the Transaction and TransactionalExecutor to ensure
proper commit/rollback behavior.
"""

import pytest
from engine.core.state import GameState
from engine.core.transaction import Transaction, TransactionalExecutor
from engine.commands.economy import GainGoldCommand, SpendGoldCommand


class TestTransaction:
    """Tests for Transaction class."""
    
    def test_transaction_commit(self):
        """Test committing transaction applies changes."""
        state = GameState()
        state.set_entity("player_1", {"gold": 100})
        
        # Create transaction
        transaction = Transaction(state)
        work_state = transaction.get_work_state()
        
        # Modify work state
        player = work_state.get_entity("player_1")
        player["gold"] = 200
        work_state.set_entity("player_1", player)
        
        # Commit
        transaction.commit()
        
        # Verify changes applied
        assert state.get_entity("player_1")["gold"] == 200
        assert transaction.is_committed
        assert not transaction.is_rolled_back
    
    def test_transaction_rollback(self):
        """Test rolling back transaction discards changes."""
        state = GameState()
        state.set_entity("player_1", {"gold": 100})
        
        # Create transaction
        transaction = Transaction(state)
        work_state = transaction.get_work_state()
        
        # Modify work state
        player = work_state.get_entity("player_1")
        player["gold"] = 200
        work_state.set_entity("player_1", player)
        
        # Rollback
        transaction.rollback()
        
        # Verify changes NOT applied
        assert state.get_entity("player_1")["gold"] == 100
        assert not transaction.is_committed
        assert transaction.is_rolled_back
    
    def test_transaction_double_commit_fails(self):
        """Test committing twice raises error."""
        state = GameState()
        transaction = Transaction(state)
        
        transaction.commit()
        
        with pytest.raises(RuntimeError, match="already committed"):
            transaction.commit()
    
    def test_transaction_double_rollback_fails(self):
        """Test rolling back twice raises error."""
        state = GameState()
        transaction = Transaction(state)
        
        transaction.rollback()
        
        with pytest.raises(RuntimeError, match="already rolled back"):
            transaction.rollback()
    
    def test_transaction_commit_after_rollback_fails(self):
        """Test committing after rollback raises error."""
        state = GameState()
        transaction = Transaction(state)
        
        transaction.rollback()
        
        with pytest.raises(RuntimeError, match="already rolled back"):
            transaction.commit()
    
    def test_transaction_rollback_after_commit_fails(self):
        """Test rolling back after commit raises error."""
        state = GameState()
        transaction = Transaction(state)
        
        transaction.commit()
        
        with pytest.raises(RuntimeError, match="already committed"):
            transaction.rollback()
    
    def test_transaction_work_state_after_finalize_fails(self):
        """Test getting work state after finalize raises error."""
        state = GameState()
        transaction = Transaction(state)
        
        transaction.commit()
        
        with pytest.raises(RuntimeError, match="already finalized"):
            transaction.get_work_state()
    
    def test_transaction_isolation(self):
        """Test transaction changes don't affect original until commit."""
        state = GameState()
        state.set_entity("player_1", {"gold": 100})
        
        transaction = Transaction(state)
        work_state = transaction.get_work_state()
        
        # Modify work state
        player = work_state.get_entity("player_1")
        player["gold"] = 200
        work_state.set_entity("player_1", player)
        
        # Original state unchanged
        assert state.get_entity("player_1")["gold"] == 100
        
        # Commit
        transaction.commit()
        
        # Now changed
        assert state.get_entity("player_1")["gold"] == 200


class TestTransactionalExecutor:
    """Tests for TransactionalExecutor."""
    
    def test_executor_commit_on_success(self):
        """Test executor commits on successful command."""
        state = GameState()
        state.set_entity("player_1", {"gold": 100})
        
        executor = TransactionalExecutor(state)
        cmd = GainGoldCommand("player_1", 50)
        
        result = executor.execute(cmd)
        
        assert result.success
        assert result.data["new_gold"] == 150
        assert state.get_entity("player_1")["gold"] == 150
    
    def test_executor_rollback_on_error(self):
        """Test executor rolls back on command error."""
        state = GameState()
        state.set_entity("player_1", {"gold": 50})
        
        executor = TransactionalExecutor(state)
        cmd = SpendGoldCommand("player_1", 100)  # Insufficient gold
        
        result = executor.execute(cmd)
        
        assert not result.success
        assert "Validation error" in result.error
        # State unchanged
        assert state.get_entity("player_1")["gold"] == 50
    
    def test_executor_rollback_on_key_error(self):
        """Test executor rolls back on missing entity."""
        state = GameState()
        
        executor = TransactionalExecutor(state)
        cmd = SpendGoldCommand("nonexistent", 100)
        
        result = executor.execute(cmd)
        
        assert not result.success
        assert "Entity not found" in result.error
    
    def test_executor_multiple_commands(self):
        """Test executing multiple commands in sequence."""
        state = GameState()
        state.set_entity("player_1", {"gold": 100})
        
        executor = TransactionalExecutor(state)
        
        # First command
        result1 = executor.execute(GainGoldCommand("player_1", 50))
        assert result1.success
        assert state.get_entity("player_1")["gold"] == 150
        
        # Second command
        result2 = executor.execute(SpendGoldCommand("player_1", 30))
        assert result2.success
        assert state.get_entity("player_1")["gold"] == 120
        
        # Third command (fails)
        result3 = executor.execute(SpendGoldCommand("player_1", 200))
        assert not result3.success
        # State unchanged from last successful command
        assert state.get_entity("player_1")["gold"] == 120

