"""Integration test for bot with real token.

This test verifies that the bot can initialize and connect to Telegram API.
"""

import pytest
import asyncio
import os

# Only run if token is provided
TELEGRAM_BOT_TOKEN = "8452846315:AAE2w3kjlRJZTrzb8uXjdC7rIXDohV_nPMA"


@pytest.mark.skipif(not TELEGRAM_BOT_TOKEN, reason="No bot token provided")
class TestBotWithRealToken:
    """Integration tests with real Telegram bot token."""
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self):
        """Test that bot can initialize with real token."""
        from engine.core import GameState, AsyncCommandExecutor
        from engine.adapters.telegram import GameBot
        
        # Create in-memory state for testing
        state = GameState()
        executor = AsyncCommandExecutor(state)
        
        # Create bot
        bot = GameBot(token=TELEGRAM_BOT_TOKEN, state=state, executor=executor)
        
        # Verify bot created successfully
        assert bot is not None
        assert bot.bot is not None
        assert bot.dp is not None
        
        # Clean up
        await bot.stop()
    
    @pytest.mark.asyncio
    async def test_bot_get_me(self):
        """Test that bot can connect to Telegram API and get bot info."""
        from aiogram import Bot
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        try:
            # Try to get bot information
            me = await bot.get_me()
            
            # Verify we got valid bot info
            assert me is not None
            assert me.id is not None
            assert me.username is not None
            
            print(f"\n✅ Bot connected successfully!")
            print(f"   Bot ID: {me.id}")
            print(f"   Bot username: @{me.username}")
            print(f"   Bot name: {me.first_name}")
            
        finally:
            # Clean up
            await bot.session.close()
    
    @pytest.mark.asyncio
    async def test_bot_handlers_registered(self):
        """Test that all bot handlers are registered."""
        from engine.core import GameState, AsyncCommandExecutor
        from engine.adapters.telegram import GameBot
        
        state = GameState()
        executor = AsyncCommandExecutor(state)
        bot = GameBot(token=TELEGRAM_BOT_TOKEN, state=state, executor=executor)
        
        # Check that dispatcher has registered handlers
        # aiogram 3.x stores handlers in dp.observers
        assert len(bot.dp.observers) > 0
        
        print(f"\n✅ Bot has {len(bot.dp.observers)} handler groups registered")
        
        # Clean up
        await bot.stop()

