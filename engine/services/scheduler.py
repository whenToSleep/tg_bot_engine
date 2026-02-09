"""Scheduler Service - Asyncio-based task scheduler for game events.

This module provides a flexible task scheduler for time-based game mechanics:
- Flash banners (limited-time gacha events)
- Daily/weekly resets
- Timed rewards
- Event start/end triggers

The scheduler uses asyncio tasks and supports:
- One-time tasks (execute once at specific time)
- Recurring tasks (execute periodically)
- Task cancellation
- Graceful shutdown

Example:
    >>> from engine.services.scheduler import get_scheduler
    >>> 
    >>> scheduler = get_scheduler()
    >>> await scheduler.start()
    >>> 
    >>> # Schedule a flash banner to expire in 2 hours
    >>> task_id = scheduler.schedule_once(
    ...     callback=expire_banner_callback,
    ...     delay_seconds=7200,  # 2 hours
    ...     task_name="expire_flash_banner_fire"
    ... )
    >>> 
    >>> # Schedule daily reset at midnight
    >>> scheduler.schedule_recurring(
    ...     callback=daily_reset_callback,
    ...     interval_seconds=86400,  # 24 hours
    ...     task_name="daily_reset"
    ... )
"""

import asyncio
from typing import Dict, Callable, Awaitable, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """Represents a scheduled task in the system.
    
    Attributes:
        task_id: Unique identifier for the task
        task_name: Human-readable name for debugging
        callback: Async function to execute
        task: asyncio.Task object
        recurring: Whether task repeats
        interval: Interval in seconds (for recurring tasks)
        created_at: When the task was created
    """
    task_id: str
    task_name: str
    callback: Callable[[], Awaitable[None]]
    task: asyncio.Task
    recurring: bool = False
    interval: Optional[float] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class SchedulerService:
    """Asyncio-based scheduler for game events and timed mechanics.
    
    This service manages all time-based game events:
    - Flash banners (appear/disappear on schedule)
    - Daily/weekly resets
    - Timed events and campaigns
    - Periodic cleanup tasks
    
    Features:
    - Non-blocking task execution
    - Automatic error handling and logging
    - Task cancellation support
    - Graceful shutdown with cleanup
    
    Example:
        >>> scheduler = SchedulerService()
        >>> await scheduler.start()
        >>> 
        >>> # One-time task
        >>> task_id = scheduler.schedule_once(
        ...     callback=my_async_function,
        ...     delay_seconds=3600
        ... )
        >>> 
        >>> # Recurring task
        >>> scheduler.schedule_recurring(
        ...     callback=cleanup_function,
        ...     interval_seconds=300  # Every 5 minutes
        ... )
        >>> 
        >>> # Cancel task
        >>> scheduler.cancel_task(task_id)
        >>> 
        >>> # Shutdown
        >>> await scheduler.shutdown()
    """
    
    def __init__(self):
        """Initialize the scheduler."""
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._task_counter = 0
        
    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        self._task_counter += 1
        return f"task_{self._task_counter}_{datetime.now().timestamp()}"
    
    async def start(self) -> None:
        """Start the scheduler.
        
        Must be called before scheduling tasks.
        """
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        logger.info("Scheduler started")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the scheduler.
        
        Cancels all active tasks and waits for cleanup.
        """
        if not self._running:
            return
        
        logger.info(f"Shutting down scheduler ({len(self._tasks)} active tasks)")
        
        # Cancel all tasks
        for task_id in list(self._tasks.keys()):
            self.cancel_task(task_id)
        
        # Wait for all tasks to complete cancellation
        if self._tasks:
            await asyncio.sleep(0.1)  # Give tasks time to clean up
        
        self._running = False
        logger.info("Scheduler shutdown complete")
    
    def schedule_once(
        self,
        callback: Callable[[], Awaitable[None]],
        delay_seconds: float,
        task_name: Optional[str] = None
    ) -> str:
        """Schedule a one-time task.
        
        Args:
            callback: Async function to execute
            delay_seconds: Delay before execution
            task_name: Optional name for debugging
            
        Returns:
            Task ID for cancellation
            
        Example:
            >>> task_id = scheduler.schedule_once(
            ...     callback=end_event,
            ...     delay_seconds=7200,  # 2 hours
            ...     task_name="end_flash_banner"
            ... )
        """
        if not self._running:
            raise RuntimeError("Scheduler not running. Call start() first.")
        
        task_id = self._generate_task_id()
        task_name = task_name or f"once_{task_id}"
        
        async def _wrapped_task():
            try:
                await asyncio.sleep(delay_seconds)
                logger.debug(f"Executing one-time task: {task_name}")
                await callback()
            except asyncio.CancelledError:
                logger.debug(f"Task cancelled: {task_name}")
            except Exception as e:
                logger.error(f"Error in task {task_name}: {e}", exc_info=True)
            finally:
                # Clean up task from registry
                self._tasks.pop(task_id, None)
        
        task = asyncio.create_task(_wrapped_task())
        
        scheduled = ScheduledTask(
            task_id=task_id,
            task_name=task_name,
            callback=callback,
            task=task,
            recurring=False
        )
        
        self._tasks[task_id] = scheduled
        logger.info(f"Scheduled one-time task '{task_name}' (delay: {delay_seconds}s)")
        
        return task_id
    
    def schedule_recurring(
        self,
        callback: Callable[[], Awaitable[None]],
        interval_seconds: float,
        task_name: Optional[str] = None,
        initial_delay: Optional[float] = None
    ) -> str:
        """Schedule a recurring task.
        
        Args:
            callback: Async function to execute
            interval_seconds: Time between executions
            task_name: Optional name for debugging
            initial_delay: Optional delay before first execution (defaults to interval)
            
        Returns:
            Task ID for cancellation
            
        Example:
            >>> task_id = scheduler.schedule_recurring(
            ...     callback=daily_reset,
            ...     interval_seconds=86400,  # 24 hours
            ...     task_name="daily_reset"
            ... )
        """
        if not self._running:
            raise RuntimeError("Scheduler not running. Call start() first.")
        
        task_id = self._generate_task_id()
        task_name = task_name or f"recurring_{task_id}"
        first_delay = initial_delay if initial_delay is not None else interval_seconds
        
        async def _wrapped_task():
            try:
                # Initial delay
                await asyncio.sleep(first_delay)
                
                while True:
                    logger.debug(f"Executing recurring task: {task_name}")
                    try:
                        await callback()
                    except Exception as e:
                        logger.error(f"Error in recurring task {task_name}: {e}", exc_info=True)
                    
                    # Wait for next execution
                    await asyncio.sleep(interval_seconds)
                    
            except asyncio.CancelledError:
                logger.debug(f"Recurring task cancelled: {task_name}")
            except Exception as e:
                logger.error(f"Fatal error in recurring task {task_name}: {e}", exc_info=True)
            finally:
                # Clean up task from registry
                self._tasks.pop(task_id, None)
        
        task = asyncio.create_task(_wrapped_task())
        
        scheduled = ScheduledTask(
            task_id=task_id,
            task_name=task_name,
            callback=callback,
            task=task,
            recurring=True,
            interval=interval_seconds
        )
        
        self._tasks[task_id] = scheduled
        logger.info(f"Scheduled recurring task '{task_name}' (interval: {interval_seconds}s)")
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task.
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            True if task was cancelled, False if not found
            
        Example:
            >>> scheduler.cancel_task("task_123_456")
            True
        """
        scheduled = self._tasks.get(task_id)
        if not scheduled:
            logger.warning(f"Task not found for cancellation: {task_id}")
            return False
        
        scheduled.task.cancel()
        logger.info(f"Cancelled task: {scheduled.task_name}")
        return True
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all active tasks.
        
        Returns:
            Dictionary mapping task_id to task info
            
        Example:
            >>> tasks = scheduler.get_active_tasks()
            >>> for task_id, info in tasks.items():
            ...     print(f"{info['name']}: {info['recurring']}")
        """
        return {
            task_id: {
                "task_id": task.task_id,
                "name": task.task_name,
                "recurring": task.recurring,
                "interval": task.interval,
                "created_at": task.created_at.isoformat(),
                "done": task.task.done()
            }
            for task_id, task in self._tasks.items()
        }
    
    def is_running(self) -> bool:
        """Check if scheduler is running.
        
        Returns:
            True if scheduler is active
        """
        return self._running


# Global singleton instance
_global_scheduler: Optional[SchedulerService] = None


def get_scheduler() -> SchedulerService:
    """Get the global scheduler instance.
    
    Returns:
        Global SchedulerService instance
        
    Example:
        >>> scheduler = get_scheduler()
        >>> await scheduler.start()
    """
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = SchedulerService()
    return _global_scheduler


def reset_scheduler() -> None:
    """Reset the global scheduler instance.
    
    Used primarily for testing.
    """
    global _global_scheduler
    _global_scheduler = None

