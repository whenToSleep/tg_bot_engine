"""Telegram adapter for the game engine.

This module provides integration with Telegram via aiogram,
converting Telegram messages and callbacks into game commands
and building appropriate responses.
"""

from .command_adapter import TelegramCommandAdapter
from .response_builder import ResponseBuilder
from .bot import GameBot
from .media_library import MediaLibrary, get_media_library, reset_media_library

__all__ = [
    'TelegramCommandAdapter',
    'ResponseBuilder',
    'GameBot',
    'MediaLibrary',
    'get_media_library',
    'reset_media_library',
]

