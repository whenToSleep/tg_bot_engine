"""Services - High-level game services and business logic.

This package contains service modules that provide complex game mechanics:
- gacha_service: Gacha system with pity mechanics
- matchmaking: PvP matchmaking and ranking
- scheduler: Asyncio-based task scheduler for events
- banner_manager: Dynamic gacha banner management
"""

try:
    from engine.services.gacha_service import (
        GachaService,
        PityConfig,
        GachaResult,
        RarityTier,
        create_gacha_service,
    )
    _GACHA_AVAILABLE = True
except ImportError:
    _GACHA_AVAILABLE = False

try:
    from engine.services.matchmaking import (
        MatchmakingService,
        MatchResult,
        RankingSystem,
    )
    _MATCHMAKING_AVAILABLE = True
except ImportError:
    _MATCHMAKING_AVAILABLE = False

try:
    from engine.services.scheduler import (
        SchedulerService,
        ScheduledTask,
        get_scheduler,
        reset_scheduler,
    )
    _SCHEDULER_AVAILABLE = True
except ImportError:
    _SCHEDULER_AVAILABLE = False

try:
    from engine.services.banner_manager import (
        BannerManager,
        BannerConfig,
        BannerState,
        BannerStatus,
        get_banner_manager,
        reset_banner_manager,
    )
    _BANNER_AVAILABLE = True
except ImportError:
    _BANNER_AVAILABLE = False

try:
    from engine.services.raid_service import (
        RaidService,
        RaidEntity,
        RaidStatus,
        AttackResult,
        get_raid_service,
        reset_raid_service,
    )
    _RAID_AVAILABLE = True
except ImportError:
    _RAID_AVAILABLE = False

__all__ = []

if _GACHA_AVAILABLE:
    __all__.extend([
        "GachaService",
        "PityConfig",
        "GachaResult",
        "RarityTier",
        "create_gacha_service",
    ])

if _MATCHMAKING_AVAILABLE:
    __all__.extend([
        "MatchmakingService",
        "MatchResult",
        "RankingSystem",
    ])

if _SCHEDULER_AVAILABLE:
    __all__.extend([
        "SchedulerService",
        "ScheduledTask",
        "get_scheduler",
        "reset_scheduler",
    ])

if _BANNER_AVAILABLE:
    __all__.extend([
        "BannerManager",
        "BannerConfig",
        "BannerState",
        "BannerStatus",
        "get_banner_manager",
        "reset_banner_manager",
    ])

if _RAID_AVAILABLE:
    __all__.extend([
        "RaidService",
        "RaidEntity",
        "RaidStatus",
        "AttackResult",
        "get_raid_service",
        "reset_raid_service",
    ])

