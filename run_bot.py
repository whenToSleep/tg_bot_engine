"""Quick start script for running the game bot.

Usage:
    python run_bot.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from engine.core import PersistentGameState, AsyncCommandExecutor
from engine.adapters import SQLiteRepository
from engine.adapters.telegram import GameBot
from engine.modules.achievements import AchievementModule
from engine.modules.progression import ProgressionModule


# Bot token - replace with your token or set TELEGRAM_BOT_TOKEN env variable
TELEGRAM_BOT_TOKEN = "8452846315:AAE2w3kjlRJZTrzb8uXjdC7rIXDohV_nPMA"


async def main():
    """Run the bot."""
    print("=" * 60)
    print("🎮 Telegram Game Bot")
    print("=" * 60)
    
    # Setup database and state
    print("📦 Initializing database...")
    db_path = "game.db"
    repo = SQLiteRepository(db_path)
    state = PersistentGameState(repo, auto_flush=True)
    
    # Create async executor
    print("⚙️  Creating command executor...")
    executor = AsyncCommandExecutor(state)
    
    # Initialize game modules
    print("🎯 Loading game modules...")
    achievement_module = AchievementModule(state)
    progression_module = ProgressionModule(state)
    
    # Create and start bot
    print("🤖 Starting bot...")
    bot = GameBot(token=TELEGRAM_BOT_TOKEN, state=state, executor=executor)
    
    print("\n" + "=" * 60)
    print("✅ Bot started successfully!")
    print("=" * 60)
    print("\n📱 Open Telegram and find: @test_game_rpg_dream_bot")
    print("\n💡 Available commands:")
    print("   /start - Begin game")
    print("   /fight - Fight a goblin")
    print("   /profile - View your stats")
    print("   /claim_daily - Get 100 gold")
    print("\n⏹️  Press Ctrl+C to stop the bot")
    print("=" * 60)
    print()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        await bot.stop()
        print("✅ Bot stopped successfully")


if __name__ == "__main__":
    asyncio.run(main())

