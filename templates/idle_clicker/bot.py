"""
Idle Clicker Bot Template
Based on tg_bot_engine

Setup:
    1. Create virtual environment:
       python -m venv venv
       
    2. Activate it:
       Windows: venv\\Scripts\\activate
       Linux/Mac: source venv/bin/activate
       
    3. Install engine:
       pip install tg-bot-engine
       pip install -r requirements.txt
    
    4. Configure:
       cp .env.example .env
       # Edit .env with your TELEGRAM_BOT_TOKEN
    
    5. Run:
       python bot.py
"""

import os
import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv

# Import engine components
from engine.core import (
    PersistentGameState,
    AsyncCommandExecutor,
    get_data_loader
)
from engine.adapters import SQLiteRepository
from engine.adapters.telegram import GameBot


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_game_data():
    """Load all game content from data/ directory."""
    logger.info("Loading game data...")
    data_loader = get_data_loader()
    
    # Set data directory to current template's data folder
    data_dir = Path(__file__).parent / "data"
    
    try:
        # Load buildings
        buildings = data_loader.load_category(
            str(data_dir / "buildings"),
            "building",
            str(data_dir / "schemas" / "building_schema.json")
        )
        logger.info(f"✓ Loaded {len(buildings)} buildings")
        
        # Load upgrades
        upgrades = data_loader.load_category(
            str(data_dir / "upgrades"),
            "upgrade",
            str(data_dir / "schemas" / "upgrade_schema.json")
        )
        logger.info(f"✓ Loaded {len(upgrades)} upgrades")
        
        logger.info("✓ Game data loaded successfully!")
        
    except Exception as e:
        logger.error(f"✗ Failed to load game data: {e}")
        raise


async def main():
    """Main entry point for the bot."""
    # Load environment variables
    load_dotenv()
    
    # Get bot token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("✗ TELEGRAM_BOT_TOKEN not found in .env file!")
        logger.info("\nTo get started:")
        logger.info("  1. Copy .env.example to .env")
        logger.info("  2. Get a bot token from @BotFather on Telegram")
        logger.info("  3. Add your token to .env file")
        logger.info("  4. Run this script again\n")
        return
    
    # Setup database
    db_path = os.getenv("DATABASE_PATH", "game.db")
    logger.info(f"Using database: {db_path}")
    repo = SQLiteRepository(db_path)
    
    # Create persistent game state
    state = PersistentGameState(repo, auto_flush=True)
    
    # Create async executor
    executor = AsyncCommandExecutor(state)
    
    # Load game content
    load_game_data()
    
    # Create and start bot
    logger.info("Starting Telegram bot...")
    bot = GameBot(token=token, state=state, executor=executor)
    
    try:
        logger.info("✓ Bot is running! Press Ctrl+C to stop.")
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.stop()
    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)
        await bot.stop()


if __name__ == "__main__":
    # Check if running in correct directory
    if not Path("data").exists():
        print("✗ Error: 'data' directory not found!")
        print("  Make sure you're running this script from the template directory")
        exit(1)
    
    # Run the bot
    asyncio.run(main())

