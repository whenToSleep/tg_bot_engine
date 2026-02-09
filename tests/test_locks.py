"""Tests for entity locking functionality.

Tests EntityLockManager to ensure proper locking, timeout handling,
and maintenance operations.
"""

import pytest
import asyncio
from engine.core.locks import EntityLockManager


@pytest.mark.asyncio
class TestEntityLockManager:
    """Tests for EntityLockManager."""
    
    async def test_lock_single_entity(self):
        """Test locking a single entity."""
        manager = EntityLockManager()
        
        async with manager.lock_entities(["player_1"]):
            # Should be locked during context
            assert manager.is_locked("player_1")
        
        # Should be unlocked after context
        assert not manager.is_locked("player_1")
    
    async def test_lock_multiple_entities(self):
        """Test locking multiple entities."""
        manager = EntityLockManager()
        
        async with manager.lock_entities(["player_1", "player_2", "mob_1"]):
            assert manager.is_locked("player_1")
            assert manager.is_locked("player_2")
            assert manager.is_locked("mob_1")
        
        assert not manager.is_locked("player_1")
        assert not manager.is_locked("player_2")
        assert not manager.is_locked("mob_1")
    
    async def test_is_locked_nonexistent_entity(self):
        """Test checking lock status of nonexistent entity."""
        manager = EntityLockManager()
        
        assert not manager.is_locked("nonexistent")
    
    async def test_acquire_timeout(self):
        """Test timeout when acquiring locks."""
        manager = EntityLockManager()
        
        # Acquire lock
        acquired = await manager.acquire(["player_1"], timeout=5.0)
        assert "player_1" in acquired
        assert manager.is_locked("player_1")
        
        # Try to acquire same lock with short timeout
        with pytest.raises(TimeoutError, match="Failed to acquire locks"):
            await manager.acquire(["player_1"], timeout=0.1)
        
        # Release
        manager.release(acquired)
        assert not manager.is_locked("player_1")
    
    async def test_release_multiple_entities(self):
        """Test releasing multiple entities."""
        manager = EntityLockManager()
        
        acquired = await manager.acquire(["e1", "e2", "e3"])
        assert all(manager.is_locked(e) for e in ["e1", "e2", "e3"])
        
        manager.release(acquired)
        assert not any(manager.is_locked(e) for e in ["e1", "e2", "e3"])
    
    async def test_release_nonexistent_lock(self):
        """Test releasing lock that doesn't exist (should not error)."""
        manager = EntityLockManager()
        
        # Should not raise error
        manager.release(["nonexistent"])
    
    async def test_release_already_released(self):
        """Test releasing already released lock (should not error)."""
        manager = EntityLockManager()
        
        acquired = await manager.acquire(["player_1"])
        manager.release(acquired)
        
        # Release again - should not error
        manager.release(acquired)
    
    async def test_sorted_lock_order(self):
        """Test locks are acquired in sorted order."""
        manager = EntityLockManager()
        
        # Request in unsorted order
        acquired = await manager.acquire(["z", "a", "m"])
        
        # Should still succeed (order handled internally)
        assert len(acquired) == 3
        
        manager.release(acquired)
    
    async def test_concurrent_lock_requests(self):
        """Test multiple concurrent lock requests."""
        manager = EntityLockManager()
        
        async def lock_and_work(entity_id: str) -> str:
            async with manager.lock_entities([entity_id]):
                await asyncio.sleep(0.01)  # Simulate work
                return f"done_{entity_id}"
        
        # Multiple concurrent requests for different entities
        results = await asyncio.gather(
            lock_and_work("e1"),
            lock_and_work("e2"),
            lock_and_work("e3")
        )
        
        assert results == ["done_e1", "done_e2", "done_e3"]
    
    async def test_clear_unused_locks(self):
        """Test clearing unused locks."""
        manager = EntityLockManager()
        
        # Create some locks
        async with manager.lock_entities(["e1", "e2"]):
            pass  # Locks created and released
        
        # Locks still exist but not held
        assert "e1" in manager._locks
        assert "e2" in manager._locks
        
        # Clear unused
        cleared = manager.clear_unused_locks()
        
        assert cleared == 2
        assert "e1" not in manager._locks
        assert "e2" not in manager._locks
    
    async def test_clear_keeps_active_locks(self):
        """Test clearing doesn't remove active locks."""
        manager = EntityLockManager()
        
        # Hold a lock
        acquired = await manager.acquire(["active"])
        
        # Create and release another
        async with manager.lock_entities(["inactive"]):
            pass
        
        # Clear unused
        cleared = manager.clear_unused_locks()
        
        # Should only clear inactive
        assert cleared == 1
        assert "active" in manager._locks
        assert "inactive" not in manager._locks
        
        # Clean up
        manager.release(acquired)
    
    async def test_acquire_partial_failure_rollback(self):
        """Test acquiring locks fails atomically."""
        manager = EntityLockManager()
        
        # Lock one entity
        acquired1 = await manager.acquire(["e1"])
        
        try:
            # Try to lock e1 and e2 (e1 already locked)
            await manager.acquire(["e1", "e2"], timeout=0.1)
            pytest.fail("Should have raised TimeoutError")
        except TimeoutError:
            # e2 should NOT be locked (rollback)
            assert not manager.is_locked("e2")
        
        manager.release(acquired1)

