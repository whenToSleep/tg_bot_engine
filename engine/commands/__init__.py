"""Built-in game commands.

This module contains pre-built commands for common game mechanics:
- Economy: Gold management
- Combat: Battle mechanics
"""

from engine.commands.economy import GainGoldCommand, SpendGoldCommand
from engine.commands.combat import AttackMobCommand

__all__ = [
    "GainGoldCommand",
    "SpendGoldCommand",
    "AttackMobCommand",
]

