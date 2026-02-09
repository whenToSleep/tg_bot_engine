"""Telegram Game Engine - Command-based game engine for Telegram bots.

This package provides a production-ready framework for creating
multiplayer turn-based games in Telegram with ACID guarantees,
transaction support, and data-driven development.

Version: 0.6.0 (Iteration 6.1 - Scheduler & Dynamic Banners)
"""

__version__ = "0.6.0"
__author__ = "TG Bot Engine Team"
__license__ = "MIT"

# Core imports
from engine.core.command import Command, CommandResult
from engine.core.state import GameState
from engine.core.executor import CommandExecutor
from engine.core.transaction import Transaction, TransactionalExecutor
from engine.core.locks import EntityLockManager
from engine.core.async_executor import AsyncCommandExecutor
from engine.core.saga import Saga, SagaBuilder, SagaStep, SagaStatus
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
    BannerActivatedEvent,
    BannerExpiredEvent,
    GachaPullEvent,
)

# Utilities
from engine.core.utils import (
    weighted_choice,
    roll_loot_table,
    gacha_pull,
    calculate_offline_progress,
    calculate_exponential_cost,
    calculate_exponential_production,
    merge_item_stacks,
    filter_entities,
)

# Stat Modifiers (Buffs/Debuffs)
from engine.core.modifiers import (
    Modifier,
    ModifierType,
    StatCalculator,
    add_modifier,
    remove_modifiers_by_source,
    has_modifier_from_source,
)

# Bonus Calculator (Idle Multipliers)
from engine.core.bonuses import (
    BonusCalculator,
    calculate_bonus_summary,
    load_bonuses_from_entity,
    save_bonuses_to_entity,
)

# Group Bonus Calculator (Synergies)
from engine.core.group_bonuses import (
    GroupBonusCalculator,
    SynergyRule,
    create_element_synergy_rule,
    create_rarity_synergy_rule,
    analyze_deck_composition,
)

# Entity Status System
from engine.core.entity_status import (
    EntityStatus,
    set_status,
    get_status,
    has_status,
    is_usable,
    is_tradable,
    get_entities_by_status,
    filter_usable,
    filter_tradable,
    StatusValidator,
)

# Unique Entity System
from engine.core.unique_entity import (
    generate_unique_id,
    create_unique_entity,
    create_multiple_entities,
    get_proto_id,
    is_same_prototype,
    group_by_prototype,
    count_by_prototype,
    UniqueEntityManager,
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

# Services (опционально)
try:
    from engine.services import (
        GachaService,
        PityConfig,
        GachaResult,
        RarityTier,
        create_gacha_service,
        MatchmakingService,
        MatchResult,
        RankingSystem,
        SchedulerService,
        ScheduledTask,
        get_scheduler,
        reset_scheduler,
        BannerManager,
        BannerConfig,
        BannerStatus,
        get_banner_manager,
        reset_banner_manager,
        RaidService,
        RaidEntity,
        RaidStatus,
        AttackResult,
        get_raid_service,
        reset_raid_service,
    )
    _SERVICES_AVAILABLE = True
except ImportError:
    _SERVICES_AVAILABLE = False

# Telegram Adapter (опционально)
try:
    from engine.adapters.telegram import (
        GameBot,
        TelegramCommandAdapter,
        ResponseBuilder,
        MediaLibrary,
        get_media_library,
        reset_media_library,
    )
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
    "Saga",
    "SagaBuilder",
    "SagaStep",
    "SagaStatus",
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
    "BannerActivatedEvent",
    "BannerExpiredEvent",
    "GachaPullEvent",
    # Utilities
    "weighted_choice",
    "roll_loot_table",
    "gacha_pull",
    "calculate_offline_progress",
    "calculate_exponential_cost",
    "calculate_exponential_production",
    "merge_item_stacks",
    "filter_entities",
    # Stat Modifiers
    "Modifier",
    "ModifierType",
    "StatCalculator",
    "add_modifier",
    "remove_modifiers_by_source",
    "has_modifier_from_source",
    # Bonus Calculator
    "BonusCalculator",
    "calculate_bonus_summary",
    "load_bonuses_from_entity",
    "save_bonuses_to_entity",
    # Group Bonus Calculator
    "GroupBonusCalculator",
    "SynergyRule",
    "create_element_synergy_rule",
    "create_rarity_synergy_rule",
    "analyze_deck_composition",
    # Entity Status
    "EntityStatus",
    "set_status",
    "get_status",
    "has_status",
    "is_usable",
    "is_tradable",
    "get_entities_by_status",
    "filter_usable",
    "filter_tradable",
    "StatusValidator",
    # Unique Entity
    "generate_unique_id",
    "create_unique_entity",
    "create_multiple_entities",
    "get_proto_id",
    "is_same_prototype",
    "group_by_prototype",
    "count_by_prototype",
    "UniqueEntityManager",
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

# Add Services to __all__ if available
if _SERVICES_AVAILABLE:
    __all__.extend([
        "GachaService",
        "PityConfig",
        "GachaResult",
        "RarityTier",
        "create_gacha_service",
        "MatchmakingService",
        "MatchResult",
        "RankingSystem",
        "SchedulerService",
        "ScheduledTask",
        "get_scheduler",
        "reset_scheduler",
        "BannerManager",
        "BannerConfig",
        "BannerStatus",
        "get_banner_manager",
        "reset_banner_manager",
        "RaidService",
        "RaidEntity",
        "RaidStatus",
        "AttackResult",
        "get_raid_service",
        "reset_raid_service",
    ])

# Add Telegram adapter to __all__ if available
if _TELEGRAM_AVAILABLE:
    __all__.extend([
        "GameBot",
        "TelegramCommandAdapter",
        "ResponseBuilder",
        "MediaLibrary",
        "get_media_library",
        "reset_media_library",
    ])

