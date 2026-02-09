"""Tests for PersistentGameState.

Tests cover:
- Automatic persistence
- Lazy loading
- Manual flush
- Integration with repository
"""

import pytest
import tempfile
import os

from engine.core import PersistentGameState
from engine.adapters import SQLiteRepository


class TestPersistentGameState:
    """Tests for PersistentGameState with SQLite backend."""
    
    def test_auto_save_on_set(self):
        """Test that entities are automatically saved when set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=True)
            
            # Set entity
            state.set_entity("player1", {"_type": "player", "gold": 100})
            
            # Verify it's in database
            loaded = repo.load("player1")
            assert loaded is not None
            assert loaded["gold"] == 100
    
    def test_lazy_loading(self):
        """Test that entities are loaded from database on first access."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Save directly to repository
            repo.save("player1", {"_type": "player", "gold": 100, "_version": 1})
            
            # Create new state instance
            state = PersistentGameState(repo)
            
            # Access entity - should be loaded from database
            player = state.get_entity("player1")
            assert player is not None
            assert player["gold"] == 100
    
    def test_manual_flush(self):
        """Test manual flush when auto_flush is disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=False)
            
            # Set entity (not auto-saved)
            state.set_entity("player1", {"_type": "player", "gold": 100})
            
            # Not in database yet
            assert repo.load("player1") is None
            
            # Manual flush
            state.flush()
            
            # Now in database
            loaded = repo.load("player1")
            assert loaded is not None
            assert loaded["gold"] == 100
    
    def test_delete_removes_from_database(self):
        """Test that deleting an entity removes it from database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=True)
            
            # Save entity
            state.set_entity("player1", {"_type": "player", "gold": 100})
            assert repo.exists("player1")
            
            # Delete entity
            state.delete_entity("player1")
            
            # Verify removed from database
            assert not repo.exists("player1")
            assert state.get_entity("player1") is None
    
    def test_exists_checks_database(self):
        """Test that exists() checks both memory and database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Save directly to repository
            repo.save("player1", {"_type": "player", "gold": 100, "_version": 1})
            
            # Create new state instance
            state = PersistentGameState(repo)
            
            # Should find entity in database
            assert state.exists("player1")
    
    def test_reload_discards_memory_changes(self):
        """Test that reload() fetches fresh data from database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=False)
            
            # Save to database
            repo.save("player1", {"_type": "player", "gold": 100, "_version": 1})
            
            # Load and modify in memory (without flushing)
            player = state.get_entity("player1")
            player["gold"] = 200
            state.set_entity("player1", player)
            
            # Reload from database
            reloaded = state.reload("player1")
            
            # Should have original value from database
            assert reloaded["gold"] == 100
    
    def test_clear_removes_all_from_database(self):
        """Test that clear() removes all entities from database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=True)
            
            # Add multiple entities
            state.set_entity("player1", {"_type": "player", "gold": 100})
            state.set_entity("player2", {"_type": "player", "gold": 200})
            state.set_entity("mob1", {"_type": "mob", "hp": 50})
            
            assert repo.count() == 3
            
            # Clear all
            state.clear()
            
            # Verify database is empty
            assert repo.count() == 0
            assert state.entity_count() == 0
    
    def test_entity_count_reflects_database(self):
        """Test that entity_count() returns count from database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=True)
            
            assert state.entity_count() == 0
            
            state.set_entity("player1", {"_type": "player", "gold": 100})
            assert state.entity_count() == 1
            
            state.set_entity("player2", {"_type": "player", "gold": 200})
            assert state.entity_count() == 2
    
    def test_version_auto_added(self):
        """Test that _version field is automatically added if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=True)
            
            # Set entity without _version
            state.set_entity("player1", {"_type": "player", "gold": 100})
            
            # Load and verify _version was added
            loaded = repo.load("player1")
            assert "_version" in loaded
            assert loaded["_version"] == 1
    
    def test_multiple_state_instances_share_database(self):
        """Test that multiple state instances can share the same database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo1 = SQLiteRepository(db_path)
            repo2 = SQLiteRepository(db_path)
            
            state1 = PersistentGameState(repo1, auto_flush=True)
            state2 = PersistentGameState(repo2, auto_flush=True)
            
            # Save with state1
            state1.set_entity("player1", {"_type": "player", "gold": 100})
            
            # Load with state2
            player = state2.get_entity("player1")
            assert player is not None
            assert player["gold"] == 100
    
    def test_batch_operations_with_manual_flush(self):
        """Test batch operations with manual flush for performance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            state = PersistentGameState(repo, auto_flush=False)
            
            # Add multiple entities without auto-flush
            for i in range(10):
                state.set_entity(f"player{i}", {"_type": "player", "gold": i * 100})
            
            # Nothing in database yet
            assert repo.count() == 0
            
            # Flush all at once
            state.flush()
            
            # All entities now in database
            assert repo.count() == 10
            
            # Verify data integrity
            for i in range(10):
                loaded = repo.load(f"player{i}")
                assert loaded["gold"] == i * 100

