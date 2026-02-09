"""Telegram bot integration with the game engine.

This module provides the main bot class that integrates aiogram
with the game's command system and state management.
"""

import time
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from engine.core import PersistentGameState, AsyncCommandExecutor
from engine.commands.spawning import SpawnMobCommand
from .command_adapter import TelegramCommandAdapter
from .response_builder import ResponseBuilder


logger = logging.getLogger(__name__)


class GameBot:
    """Telegram bot for the game.
    
    Handles all Telegram interactions and converts them into game commands.
    
    Example:
        >>> from engine.core import PersistentGameState, AsyncCommandExecutor
        >>> from engine.adapters import SQLiteRepository
        >>> 
        >>> repo = SQLiteRepository("game.db")
        >>> state = PersistentGameState(repo, auto_flush=True)
        >>> executor = AsyncCommandExecutor(state)
        >>> 
        >>> bot = GameBot(token="YOUR_TOKEN", state=state, executor=executor)
        >>> await bot.start()
    """
    
    def __init__(
        self,
        token: str,
        state: PersistentGameState,
        executor: AsyncCommandExecutor
    ):
        """Initialize game bot.
        
        Args:
            token: Telegram bot token
            state: Persistent game state
            executor: Async command executor
        """
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.state = state
        self.executor = executor
        self.adapter = TelegramCommandAdapter(executor)
        self.response_builder = ResponseBuilder()
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all message and callback handlers."""
        
        @self.dp.message(Command("start"))
        async def start_handler(message: Message):
            """Handle /start command - create player if needed."""
            user_id = str(message.from_user.id)
            
            # Check if player exists
            player = self.state.get_entity(user_id)
            
            if not player:
                # Create new player
                self.state.set_entity(user_id, {
                    "_type": "player",
                    "gold": 0,
                    "level": 1,
                    "exp": 0,
                    "attack": 10,
                    "_version": 1
                })
                logger.info(f"Created new player: {user_id}")
            
            # Send welcome message
            response = self.response_builder.build_welcome()
            await message.answer(response['text'])
        
        @self.dp.message(Command("profile"))
        async def profile_handler(message: Message):
            """Handle /profile command - show player stats."""
            user_id = str(message.from_user.id)
            
            # Get player data
            player = self.state.get_entity(user_id)
            
            if not player:
                await message.answer(
                    "❌ Вы еще не зарегистрированы!\n"
                    "Используйте /start для начала игры."
                )
                return
            
            # Build and send stats
            response = self.response_builder.build_player_stats(player)
            await message.answer(response['text'])
        
        @self.dp.message(Command("fight"))
        async def fight_handler(message: Message):
            """Handle /fight command - spawn a mob."""
            user_id = str(message.from_user.id)
            
            # Check if player exists
            player = self.state.get_entity(user_id)
            if not player:
                await message.answer(
                    "❌ Вы еще не зарегистрированы!\n"
                    "Используйте /start для начала игры."
                )
                return
            
            # Generate unique mob ID
            mob_id = f"mob_{user_id}_{int(time.time() * 1000)}"
            mob_template_id = "goblin_warrior"
            
            # Spawn mob using command
            spawn_cmd = SpawnMobCommand(
                mob_template_id=mob_template_id,
                instance_id=mob_id
            )
            
            result = await self.executor.execute(spawn_cmd)
            
            if result.success:
                response = self.response_builder.build_mob_spawn_result(
                    result,
                    mob_template_id
                )
                await message.answer(
                    response['text'],
                    reply_markup=response['reply_markup']
                )
            else:
                response = self.response_builder.build_error(result.error)
                await message.answer(response['text'])
        
        @self.dp.message(Command("claim_daily"))
        async def claim_daily_handler(message: Message):
            """Handle /claim_daily command - give daily reward."""
            result = await self.adapter.handle_command(message)
            response = self.response_builder.build_gold_result(result)
            await message.answer(response['text'])
        
        @self.dp.callback_query(F.data.startswith("attack:"))
        async def attack_callback_handler(callback: CallbackQuery):
            """Handle attack button callbacks."""
            # Extract mob_id from callback data
            mob_id = callback.data.split(":")[1]
            
            # Execute attack command
            result = await self.adapter.handle_callback(callback)
            
            # Build response
            response = self.response_builder.build_combat_result(result, mob_id)
            
            # Edit message
            try:
                await callback.message.edit_text(
                    text=response['text'],
                    reply_markup=response['reply_markup']
                )
            except Exception as e:
                logger.error(f"Failed to edit message: {e}")
            
            # Answer callback to remove loading state
            await callback.answer()
        
        @self.dp.callback_query(F.data.startswith("buy:"))
        async def buy_callback_handler(callback: CallbackQuery):
            """Handle buy button callbacks."""
            result = await self.adapter.handle_callback(callback)
            response = self.response_builder.build_gold_result(result)
            
            try:
                await callback.message.edit_text(
                    text=response['text'],
                    reply_markup=response['reply_markup']
                )
            except Exception as e:
                logger.error(f"Failed to edit message: {e}")
            
            await callback.answer()
    
    async def start(self):
        """Start the bot (blocking call)."""
        logger.info("Starting bot...")
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("Stopping bot...")
        await self.bot.session.close()

