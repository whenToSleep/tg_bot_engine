"""Services - High-level game services and business logic.

This package contains service modules that provide complex game mechanics:
- gacha_service: Gacha system with pity mechanics
- matchmaking: PvP matchmaking and ranking
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

