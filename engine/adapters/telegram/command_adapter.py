"""Command adapter for converting Telegram events into game commands.

This module bridges Telegram messages/callbacks and the game's command system.
"""

from typing import Optional
from aiogram import types

from engine.core import AsyncCommandExecutor, CommandResult
from engine.commands.economy import GainGoldCommand, SpendGoldCommand
from engine.commands.combat import AttackMobCommand
from engine.commands.spawning import SpawnMobCommand, SpawnItemCommand


class TelegramCommandAdapter:
    """Adapter that converts Telegram events into game commands.
    
    Handles:
    - Text commands (e.g., /claim_daily)
    - Callback queries (e.g., attack:mob_123)
    - Parameter parsing and validation
    
    Example:
        >>> adapter = TelegramCommandAdapter(executor)
        >>> result = await adapter.handle_callback(callback_query)
    """
    
    def __init__(self, executor: AsyncCommandExecutor):
        """Initialize adapter with command executor.
        
        Args:
            executor: Async command executor for running game commands
        """
        self.executor = executor
    
    async def handle_callback(self, callback: types.CallbackQuery) -> CommandResult:
        """Convert callback query into command and execute it.
        
        Supported callback formats:
        - "attack:mob_id" - Attack a mob
        - "buy:item_id:price" - Buy an item
        
        Args:
            callback: Telegram callback query
            
        Returns:
            Result of command execution
            
        Raises:
            ValueError: If callback format is unknown
        """
        user_id = str(callback.from_user.id)
        data = callback.data
        
        if not data:
            return CommandResult.error_result("Empty callback data")
        
        # Parse callback_data
        parts = data.split(":")
        action = parts[0]
        
        if action == "attack":
            if len(parts) < 2:
                return CommandResult.error_result("Missing mob_id in attack callback")
            
            mob_id = parts[1]
            command = AttackMobCommand(user_id, mob_id)
            result = await self.executor.execute(command)
            return result
        
        elif action == "buy":
            if len(parts) < 3:
                return CommandResult.error_result("Missing item_id or price in buy callback")
            
            item_id = parts[1]
            try:
                price = int(parts[2])
            except ValueError:
                return CommandResult.error_result("Invalid price format")
            
            command = SpendGoldCommand(user_id, price)
            result = await self.executor.execute(command)
            
            # If purchase successful, spawn item
            if result.success:
                # Note: In real game, would spawn into player inventory
                # For now, just confirm purchase
                result.data['item_id'] = item_id
            
            return result
        
        else:
            return CommandResult.error_result(f"Unknown callback action: {action}")
    
    async def handle_command(self, message: types.Message) -> CommandResult:
        """Convert text command into game command and execute it.
        
        Supported commands:
        - /claim_daily - Claim daily gold reward
        
        Args:
            message: Telegram message with command
            
        Returns:
            Result of command execution
            
        Raises:
            ValueError: If command is unknown
        """
        user_id = str(message.from_user.id)
        text = message.text
        
        if not text:
            return CommandResult.error_result("Empty command")
        
        if text == "/claim_daily":
            # Daily reward: 100 gold
            command = GainGoldCommand(user_id, 100)
            result = await self.executor.execute(command)
            return result
        
        else:
            return CommandResult.error_result(f"Unknown command: {text}")
    
    def parse_command_args(self, text: str) -> tuple[str, list[str]]:
        """Parse command and its arguments.
        
        Args:
            text: Command text (e.g., "/buy sword 100")
            
        Returns:
            Tuple of (command, args_list)
            
        Example:
            >>> parse_command_args("/buy sword 100")
            ('/buy', ['sword', '100'])
        """
        parts = text.split()
        command = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        return command, args

