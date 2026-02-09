"""Core components of the game engine.

This module contains the fundamental building blocks:
- Command: Base class for all game commands
- GameState: In-memory state manager
- CommandExecutor: Command execution engine
- Repository: Abstract persistence interface
- PersistentGameState: State with automatic database persistence
- Transaction: Transaction management
- Locks: Entity locking for concurrency
"""

from engine.core.command import Command, CommandResult
from engine.core.state import GameState
from engine.core.executor import CommandExecutor
from engine.core.repository import EntityRepository
from engine.core.persistent_state import PersistentGameState
from engine.core.transaction import Transaction, TransactionManager
from engine.core.locks import EntityLockManager
from engine.core.async_executor import AsyncCommandExecutor

__all__ = [
    "Command",
    "CommandResult",
    "GameState",
    "CommandExecutor",
    "EntityRepository",
    "PersistentGameState",
    "Transaction",
    "TransactionManager",
    "EntityLockManager",
    "AsyncCommandExecutor",
]

