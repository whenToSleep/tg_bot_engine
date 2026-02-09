"""Game modules - Modular game systems built on events.

Modules subscribe to events and react to game changes without
tight coupling to other systems.
"""

from engine.modules.achievements import AchievementModule
from engine.modules.progression import ProgressionModule

__all__ = [
    "AchievementModule",
    "ProgressionModule",
]

