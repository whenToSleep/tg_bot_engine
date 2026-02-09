"""Telegram Game Engine - Command-based game engine for Telegram bots.

This package provides a production-ready framework for creating
multiplayer turn-based games in Telegram with ACID guarantees,
transaction support, and data-driven development.

Version: 0.5.5 (Iteration 5.5 - Engine Packaging)
"""

__version__ = "0.5.5"
__author__ = "TG Bot Engine Team"
__license__ = "MIT"

# Core imports
from engine.core.command import Command, CommandResult
from engine.core.state import GameState
from engine.core.executor import CommandExecutor
from engine.core.transaction import Transaction, TransactionalExecutor
from engine.core.locks import EntityLockManager
from engine.core.async_executor import AsyncCommandExecutor
from engine.core.data_loader import (
    DataLoader,
    get_global_loader,
    reset_global_loader,
    DataLoaderError,
    SchemaNotFoundError,
    DataValidationError,
)
from engine.core.events import (
    Event,
    EventBus,
    get_event_bus,
    reset_event_bus,
    event_bus,
    MobKilledEvent,
    PlayerLevelUpEvent,
    GoldChangedEvent,
    AchievementUnlockedEvent,
    ItemSpawnedEvent,
    MobSpawnedEvent,
)

# Persistence
from engine.core.repository import EntityRepository
from engine.core.persistent_state import PersistentGameState
from engine.adapters.sqlite_repository import SQLiteRepository

# Modules
from engine.modules import AchievementModule, ProgressionModule

# Commands (основные)
from engine.commands.economy import GainGoldCommand, SpendGoldCommand
from engine.commands.combat import AttackMobCommand
from engine.commands.spawning import SpawnMobCommand, SpawnItemCommand

# Telegram Adapter (опционально)
try:
    from engine.adapters.telegram import GameBot, TelegramCommandAdapter, ResponseBuilder
    _TELEGRAM_AVAILABLE = True
except ImportError:
    _TELEGRAM_AVAILABLE = False

__all__ = [
    # Metadata
    "__version__",
    "__author__",
    "__license__",
    # Core
    "Command",
    "CommandResult",
    "GameState",
    "CommandExecutor",
    "Transaction",
    "TransactionalExecutor",
    "EntityLockManager",
    "AsyncCommandExecutor",
    # Persistence
    "EntityRepository",
    "PersistentGameState",
    "SQLiteRepository",
    # Data
    "DataLoader",
    "get_global_loader",
    "reset_global_loader",
    "DataLoaderError",
    "SchemaNotFoundError",
    "DataValidationError",
    # Events
    "Event",
    "EventBus",
    "get_event_bus",
    "reset_event_bus",
    "event_bus",
    "MobKilledEvent",
    "PlayerLevelUpEvent",
    "GoldChangedEvent",
    "AchievementUnlockedEvent",
    "ItemSpawnedEvent",
    "MobSpawnedEvent",
    # Modules
    "AchievementModule",
    "ProgressionModule",
    # Commands
    "GainGoldCommand",
    "SpendGoldCommand",
    "AttackMobCommand",
    "SpawnMobCommand",
    "SpawnItemCommand",
]

# Add Telegram adapter to __all__ if available
if _TELEGRAM_AVAILABLE:
    __all__.extend(["GameBot", "TelegramCommandAdapter", "ResponseBuilder"])

