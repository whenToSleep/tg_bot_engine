"""Integration tests for persistence layer.

Tests cover:
- Commands with persistent state
- Transactions with database persistence
- Crash recovery scenarios
- Optimistic locking in real scenarios
"""

import pytest
import tempfile
import os

from engine.core import PersistentGameState, CommandExecutor, Transaction, TransactionManager
from engine.adapters import SQLiteRepository
from engine.commands.economy import GainGoldCommand, SpendGoldCommand


class TestPersistenceIntegration:
    """Integration tests for persistence with commands and transactions."""
    
    def test_command_execution_persists(self):
        """Test that command execution persists changes to database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=True)
            
            # Create player
            state.set_entity("player1", {"_type": "player", "gold": 100})
            
            # Execute command
            executor = CommandExecutor()
            cmd = GainGoldCommand("player1", 50)
            result = executor.execute(cmd, state)
            
            assert result.success
            
            # Verify persisted to database
            loaded = repo.load("player1")
            assert loaded["gold"] == 150
    
    def test_transaction_commit_persists(self):
        """Test that transaction commit persists all changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=False)
            
            # Create player
            state.set_entity("player1", {"_type": "player", "gold": 100})
            state.flush()
            
            # Start transaction
            tx_manager = TransactionManager(state)
            tx = tx_manager.begin()
            
            # Get work state from transaction
            work_state = tx.get_work_state()
            
            # Execute commands on work state
            executor = CommandExecutor()
            cmd1 = GainGoldCommand("player1", 50)
            cmd2 = SpendGoldCommand("player1", 30)
            
            executor.execute(cmd1, work_state)
            executor.execute(cmd2, work_state)
            
            # Commit transaction (applies changes to original state)
            tx.commit()
            
            # Flush to database
            state.flush()
            
            # Verify final state in database
            loaded = repo.load("player1")
            assert loaded["gold"] == 120  # 100 + 50 - 30
    
    def test_transaction_rollback_prevents_persistence(self):
        """Test that transaction rollback prevents changes from being persisted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=False)
            
            # Create player
            state.set_entity("player1", {"_type": "player", "gold": 100})
            state.flush()
            
            # Start transaction
            tx_manager = TransactionManager(state)
            tx = tx_manager.begin()
            
            # Get work state
            work_state = tx.get_work_state()
            
            # Execute command on work state
            executor = CommandExecutor()
            cmd = GainGoldCommand("player1", 50)
            executor.execute(cmd, work_state)
            
            # Rollback (discard changes)
            tx.rollback()
            
            # Verify database unchanged
            loaded = repo.load("player1")
            assert loaded["gold"] == 100
    
    def test_crash_recovery_scenario(self):
        """Test recovery after simulated crash (state loss)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            
            # Session 1: Save data
            repo1 = SQLiteRepository(db_path)
            state1 = PersistentGameState(repo1, auto_flush=True)
            state1.set_entity("player1", {"_type": "player", "gold": 100, "level": 5})
            state1.set_entity("player2", {"_type": "player", "gold": 200, "level": 10})
            
            # Simulate crash - lose state1
            del state1
            del repo1
            
            # Session 2: Recover from database
            repo2 = SQLiteRepository(db_path)
            state2 = PersistentGameState(repo2, auto_flush=True)
            
            # Verify all data recovered
            player1 = state2.get_entity("player1")
            player2 = state2.get_entity("player2")
            
            assert player1 is not None
            assert player1["gold"] == 100
            assert player1["level"] == 5
            
            assert player2 is not None
            assert player2["gold"] == 200
            assert player2["level"] == 10
    
    def test_optimistic_locking_in_command_execution(self):
        """Test optimistic locking prevents conflicts in concurrent scenarios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Create initial state
            state1 = PersistentGameState(repo, auto_flush=True)
            state1.set_entity("player1", {"_type": "player", "gold": 100})
            
            # Simulate two concurrent sessions
            state2 = PersistentGameState(repo, auto_flush=True)
            state3 = PersistentGameState(repo, auto_flush=True)
            
            # Both load the same player
            player2 = state2.get_entity("player1")
            player3 = state3.get_entity("player1")
            
            # Session 2 modifies and saves
            executor = CommandExecutor()
            cmd2 = GainGoldCommand("player1", 50)
            result2 = executor.execute(cmd2, state2)
            assert result2.success
            
            # Session 3 tries to modify with stale version
            player3["gold"] = 150
            
            with pytest.raises(ValueError, match="Optimistic lock failed"):
                state3.set_entity("player1", player3)
    
    def test_multiple_commands_atomic_persistence(self):
        """Test that multiple commands in a transaction persist atomically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=False)
            
            # Create two players
            state.set_entity("player1", {"_type": "player", "gold": 100})
            state.set_entity("player2", {"_type": "player", "gold": 50})
            state.flush()
            
            # Transaction: transfer gold from player1 to player2
            tx_manager = TransactionManager(state)
            tx = tx_manager.begin()
            
            # Get work state
            work_state = tx.get_work_state()
            
            executor = CommandExecutor()
            
            # Player 1 loses gold
            cmd1 = SpendGoldCommand("player1", 30)
            result1 = executor.execute(cmd1, work_state)
            assert result1.success
            
            # Player 2 gains gold
            cmd2 = GainGoldCommand("player2", 30)
            result2 = executor.execute(cmd2, work_state)
            assert result2.success
            
            # Commit transaction
            tx.commit()
            
            # Flush to database
            state.flush()
            
            # Verify both changes persisted atomically
            loaded1 = repo.load("player1")
            loaded2 = repo.load("player2")
            
            assert loaded1["gold"] == 70  # 100 - 30
            assert loaded2["gold"] == 80  # 50 + 30
    
    def test_failed_command_doesnt_persist(self):
        """Test that failed commands don't persist changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=False)
            
            # Create player with insufficient gold
            state.set_entity("player1", {"_type": "player", "gold": 10})
            state.flush()
            
            # Start transaction
            tx_manager = TransactionManager(state)
            tx = tx_manager.begin()
            
            # Get work state
            work_state = tx.get_work_state()
            
            # Try to spend more gold than available
            executor = CommandExecutor()
            cmd = SpendGoldCommand("player1", 50)
            result = executor.execute(cmd, work_state)
            
            assert not result.success
            
            # Rollback
            tx.rollback()
            
            # Verify database unchanged
            loaded = repo.load("player1")
            assert loaded["gold"] == 10
    
    def test_persistence_with_complex_entities(self):
        """Test persistence of complex nested entity structures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=True)
            
            # Create complex player entity
            player_data = {
                "_type": "player",
                "name": "Hero",
                "gold": 100,
                "inventory": {
                    "items": [
                        {"id": "sword", "damage": 10, "durability": 100},
                        {"id": "shield", "defense": 5, "durability": 80}
                    ],
                    "capacity": 20,
                    "weight": 15
                },
                "stats": {
                    "strength": 10,
                    "agility": 15,
                    "intelligence": 8,
                    "vitality": 12
                },
                "quests": {
                    "active": ["quest_1", "quest_2"],
                    "completed": ["quest_0"]
                }
            }
            
            state.set_entity("player1", player_data)
            
            # Reload from database
            state2 = PersistentGameState(repo, auto_flush=True)
            loaded = state2.get_entity("player1")
            
            # Verify complex structure preserved
            assert loaded["name"] == "Hero"
            assert loaded["inventory"]["capacity"] == 20
            assert len(loaded["inventory"]["items"]) == 2
            assert loaded["inventory"]["items"][0]["damage"] == 10
            assert loaded["stats"]["strength"] == 10
            assert "quest_1" in loaded["quests"]["active"]
    
    def test_concurrent_reads_no_conflict(self):
        """Test that concurrent reads don't cause conflicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Create initial data
            state1 = PersistentGameState(repo, auto_flush=True)
            state1.set_entity("player1", {"_type": "player", "gold": 100})
            
            # Multiple concurrent readers
            state2 = PersistentGameState(repo, auto_flush=True)
            state3 = PersistentGameState(repo, auto_flush=True)
            state4 = PersistentGameState(repo, auto_flush=True)
            
            # All read the same entity
            player2 = state2.get_entity("player1")
            player3 = state3.get_entity("player1")
            player4 = state4.get_entity("player1")
            
            # All should have the same data
            assert player2["gold"] == 100
            assert player3["gold"] == 100
            assert player4["gold"] == 100

