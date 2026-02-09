"""Locks module - Entity locking for concurrency control.

Provides entity-level locking to prevent race conditions
in concurrent command execution.
"""

import asyncio
from typing import List, Dict
from contextlib import asynccontextmanager


class EntityLockManager:
    """Manager for entity-level locks.
    
    Prevents race conditions by locking entities during command execution.
    Uses sorted locking order to prevent deadlocks.
    
    Example:
        >>> lock_manager = EntityLockManager()
        >>> async with lock_manager.lock_entities(["player_1", "mob_1"]):
        ...     # Work with entities safely
        ...     pass
    """
    
    def __init__(self) -> None:
        """Initialize lock manager."""
        self._locks: Dict[str, asyncio.Lock] = {}
        self._main_lock = asyncio.Lock()
    
    async def acquire(self, entity_ids: List[str], timeout: float = 5.0) -> List[str]:
        """Acquire locks for entities.
        
        Args:
            entity_ids: List of entity IDs to lock
            timeout: Timeout in seconds for acquiring locks
            
        Returns:
            List of acquired entity IDs
            
        Raises:
            TimeoutError: If couldn't acquire all locks within timeout
            
        Note:
            Locks are acquired in sorted order to prevent deadlocks.
        """
        # Sort IDs to prevent deadlock
        sorted_ids = sorted(entity_ids)
        acquired: List[str] = []
        
        try:
            for entity_id in sorted_ids:
                # Ensure lock exists
                async with self._main_lock:
                    if entity_id not in self._locks:
                        self._locks[entity_id] = asyncio.Lock()
                
                # Acquire with timeout
                lock = self._locks[entity_id]
                try:
                    await asyncio.wait_for(lock.acquire(), timeout=timeout)
                    acquired.append(entity_id)
                except asyncio.TimeoutError:
                    # Timeout - release all acquired locks
                    for acquired_id in acquired:
                        self._locks[acquired_id].release()
                    raise TimeoutError(
                        f"Failed to acquire locks for {entity_ids} within {timeout}s"
                    )
            
            return acquired
            
        except Exception:
            # Any error - release acquired locks
            for acquired_id in acquired:
                if acquired_id in self._locks:
                    self._locks[acquired_id].release()
            raise
    
    def release(self, entity_ids: List[str]) -> None:
        """Release locks for entities.
        
        Args:
            entity_ids: List of entity IDs to unlock
        """
        for entity_id in entity_ids:
            if entity_id in self._locks:
                try:
                    self._locks[entity_id].release()
                except RuntimeError:
                    # Lock not acquired - ignore
                    pass
    
    @asynccontextmanager
    async def lock_entities(self, entity_ids: List[str], timeout: float = 5.0):
        """Context manager for entity locking.
        
        Args:
            entity_ids: List of entity IDs to lock
            timeout: Timeout in seconds
            
        Yields:
            None (locks are held during context)
            
        Example:
            >>> async with lock_manager.lock_entities(["p1", "p2"]):
            ...     # Work with p1 and p2
            ...     pass
        """
        acquired = await self.acquire(entity_ids, timeout)
        try:
            yield
        finally:
            self.release(acquired)
    
    def is_locked(self, entity_id: str) -> bool:
        """Check if entity is currently locked.
        
        Args:
            entity_id: Entity ID to check
            
        Returns:
            True if locked, False otherwise
        """
        if entity_id not in self._locks:
            return False
        return self._locks[entity_id].locked()
    
    def clear_unused_locks(self) -> int:
        """Clear locks that are not currently held.
        
        Returns:
            Number of locks cleared
            
        Note:
            This is a maintenance operation to prevent memory leaks.
        """
        to_remove = []
        for entity_id, lock in self._locks.items():
            if not lock.locked():
                to_remove.append(entity_id)
        
        for entity_id in to_remove:
            del self._locks[entity_id]
        
        return len(to_remove)

