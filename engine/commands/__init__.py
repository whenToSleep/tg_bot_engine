"""Built-in game commands.

This module contains pre-built commands for common game mechanics:
- Economy: Gold management
- Combat: Battle mechanics
- Gacha: Banner management and pulls
"""

from engine.commands.economy import GainGoldCommand, SpendGoldCommand
from engine.commands.combat import AttackMobCommand

try:
    from engine.commands.gacha_commands import (
        GachaPullCommand,
        CreateBannerCommand,
        ScheduleBannerCommand,
        ExpireBannerCommand,
        ActivateBannerCommand,
    )
    _GACHA_COMMANDS_AVAILABLE = True
except ImportError:
    _GACHA_COMMANDS_AVAILABLE = False

try:
    from engine.commands.fusion_commands import (
        CardFusionCommand,
        ItemCraftingCommand,
        UpgradeCommand,
    )
    _FUSION_COMMANDS_AVAILABLE = True
except ImportError:
    _FUSION_COMMANDS_AVAILABLE = False

__all__ = [
    "GainGoldCommand",
    "SpendGoldCommand",
    "AttackMobCommand",
]

if _GACHA_COMMANDS_AVAILABLE:
    __all__.extend([
        "GachaPullCommand",
        "CreateBannerCommand",
        "ScheduleBannerCommand",
        "ExpireBannerCommand",
        "ActivateBannerCommand",
    ])

if _FUSION_COMMANDS_AVAILABLE:
    __all__.extend([
        "CardFusionCommand",
        "ItemCraftingCommand",
        "UpgradeCommand",
    ])

