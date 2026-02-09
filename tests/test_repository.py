"""Tests for EntityRepository implementations.

Tests cover:
- Basic CRUD operations
- Optimistic locking
- Batch operations
- Data integrity
"""

import pytest
import tempfile
import os
from pathlib import Path

from engine.adapters import SQLiteRepository


class TestSQLiteRepository:
    """Tests for SQLiteRepository implementation."""
    
    def test_save_and_load(self):
        """Test basic save and load operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Save entity
            entity_data = {
                "_type": "player",
                "gold": 100,
                "level": 5,
                "_version": 1
            }
            repo.save("player1", entity_data)
            
            # Load entity
            loaded = repo.load("player1")
            
            assert loaded is not None
            assert loaded["gold"] == 100
            assert loaded["level"] == 5
            assert loaded["_type"] == "player"
            assert loaded["_version"] == 1
    
    def test_load_nonexistent(self):
        """Test loading non-existent entity returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            loaded = repo.load("nonexistent")
            assert loaded is None
    
    def test_delete(self):
        """Test entity deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Save and verify
            repo.save("player1", {"_type": "player", "gold": 100, "_version": 1})
            assert repo.exists("player1")
            
            # Delete and verify
            repo.delete("player1")
            assert not repo.exists("player1")
            assert repo.load("player1") is None
    
    def test_exists(self):
        """Test entity existence check."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            assert not repo.exists("player1")
            
            repo.save("player1", {"_type": "player", "gold": 100, "_version": 1})
            assert repo.exists("player1")
    
    def test_update_increments_version(self):
        """Test that updating an entity increments its version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Save initial version
            data = {"_type": "player", "gold": 100, "_version": 1}
            repo.save("player1", data)
            
            # Load and update
            loaded = repo.load("player1")
            assert loaded["_version"] == 1
            
            loaded["gold"] = 200
            repo.save("player1", loaded)
            
            # Verify version incremented
            loaded2 = repo.load("player1")
            assert loaded2["_version"] == 2
            assert loaded2["gold"] == 200
    
    def test_optimistic_locking_prevents_conflicts(self):
        """Test that optimistic locking prevents concurrent modification conflicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Save initial entity
            data_v1 = {"_type": "player", "gold": 100, "_version": 1}
            repo.save("player1", data_v1)
            
            # Simulate two concurrent readers
            thread1_data = repo.load("player1")
            thread2_data = repo.load("player1")
            
            # Thread 1 successfully updates
            thread1_data["gold"] = 200
            repo.save("player1", thread1_data)
            
            # Thread 2 tries to update with stale version
            thread2_data["gold"] = 150
            
            with pytest.raises(ValueError, match="Optimistic lock failed"):
                repo.save("player1", thread2_data)
    
    def test_list_by_type(self):
        """Test listing entities by type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Save multiple entities of different types
            repo.save("player1", {"_type": "player", "name": "Alice", "_version": 1})
            repo.save("player2", {"_type": "player", "name": "Bob", "_version": 1})
            repo.save("mob1", {"_type": "mob", "name": "Goblin", "_version": 1})
            repo.save("mob2", {"_type": "mob", "name": "Orc", "_version": 1})
            repo.save("item1", {"_type": "item", "name": "Sword", "_version": 1})
            
            # List by type
            players = repo.list_by_type("player")
            mobs = repo.list_by_type("mob")
            items = repo.list_by_type("item")
            
            assert len(players) == 2
            assert "player1" in players
            assert "player2" in players
            
            assert len(mobs) == 2
            assert "mob1" in mobs
            assert "mob2" in mobs
            
            assert len(items) == 1
            assert "item1" in items
    
    def test_count(self):
        """Test entity count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            assert repo.count() == 0
            
            repo.save("player1", {"_type": "player", "gold": 100, "_version": 1})
            assert repo.count() == 1
            
            repo.save("player2", {"_type": "player", "gold": 200, "_version": 1})
            assert repo.count() == 2
            
            repo.delete("player1")
            assert repo.count() == 1
    
    def test_clear(self):
        """Test clearing all entities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Add multiple entities
            repo.save("player1", {"_type": "player", "gold": 100, "_version": 1})
            repo.save("player2", {"_type": "player", "gold": 200, "_version": 1})
            repo.save("mob1", {"_type": "mob", "hp": 50, "_version": 1})
            
            assert repo.count() == 3
            
            # Clear all
            repo.clear()
            
            assert repo.count() == 0
            assert not repo.exists("player1")
            assert not repo.exists("player2")
            assert not repo.exists("mob1")
    
    def test_unicode_data(self):
        """Test saving and loading unicode data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Save entity with unicode characters
            entity_data = {
                "_type": "player",
                "name": "Игрок",
                "description": "Герой с мечом ⚔️",
                "_version": 1
            }
            repo.save("player1", entity_data)
            
            # Load and verify
            loaded = repo.load("player1")
            assert loaded["name"] == "Игрок"
            assert loaded["description"] == "Герой с мечом ⚔️"
    
    def test_complex_nested_data(self):
        """Test saving and loading complex nested data structures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = SQLiteRepository(db_path)
            
            # Save entity with nested data
            entity_data = {
                "_type": "player",
                "inventory": {
                    "items": [
                        {"id": "sword", "quantity": 1},
                        {"id": "potion", "quantity": 5}
                    ],
                    "capacity": 20
                },
                "stats": {
                    "strength": 10,
                    "agility": 15,
                    "intelligence": 8
                },
                "_version": 1
            }
            repo.save("player1", entity_data)
            
            # Load and verify
            loaded = repo.load("player1")
            assert loaded["inventory"]["capacity"] == 20
            assert len(loaded["inventory"]["items"]) == 2
            assert loaded["stats"]["strength"] == 10
    
    def test_persistence_across_instances(self):
        """Test that data persists across repository instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            
            # Save with first instance
            repo1 = SQLiteRepository(db_path)
            repo1.save("player1", {"_type": "player", "gold": 100, "_version": 1})
            
            # Load with second instance
            repo2 = SQLiteRepository(db_path)
            loaded = repo2.load("player1")
            
            assert loaded is not None
            assert loaded["gold"] == 100

