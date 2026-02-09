"""Telegram adapter for the game engine.

This module provides integration with Telegram via aiogram,
converting Telegram messages and callbacks into game commands
and building appropriate responses.
"""

from .command_adapter import TelegramCommandAdapter
from .response_builder import ResponseBuilder
from .bot import GameBot

__all__ = [
    'TelegramCommandAdapter',
    'ResponseBuilder',
    'GameBot',
]

