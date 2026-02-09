# RPG Template for Telegram Bot Engine

This template provides a ready-to-use structure for creating a turn-based RPG bot on Telegram.

## Features

✨ **Included Systems:**
- ⚔️ Combat system with mobs and abilities
- 🎒 Inventory and equipment system
- 📊 Player progression (XP and levels)
- 🏆 Achievements system
- 💰 Economy system
- 📦 Data-driven content (JSON)

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
cd ../..  # Go to tg_bot_engine root
pip install -e .  # Install engine
cd templates/rpg
pip install -r requirements.txt
```

### 2. Configure Bot

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your bot token
# Get token from @BotFather on Telegram
```

### 3. Customize Content

Remove example files and create your own:

```bash
# Remove examples
rm data/mobs/_example_*.json
rm data/items/_example_*.json

# Create your own mobs in data/mobs/
# Create your own items in data/items/
```

See [data/README.md](data/README.md) for content creation guide.

### 4. Run Bot

```bash
python bot.py
```

## Project Structure

```
templates/rpg/
├── data/              # Game content (JSON files)
│   ├── schemas/       # Validation schemas
│   ├── mobs/          # Enemy definitions
│   ├── items/         # Item definitions
│   ├── quests/        # Quest definitions (optional)
│   └── locations/     # Location definitions (optional)
├── bot.py             # Main bot file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
└── README.md          # This file
```

## Customization Guide

### Adding New Mobs

Create `data/mobs/my_mob.json`:

```json
{
  "id": "dragon",
  "name": "Ancient Dragon",
  "hp": 1000,
  "attack": 75,
  "defense": 30,
  "gold_reward": 1000,
  "experience_reward": 500,
  "level": 20,
  "tags": ["boss", "dragon", "legendary"]
}
```

### Adding New Items

Create `data/items/my_item.json`:

```json
{
  "id": "legendary_sword",
  "name": "Excalibur",
  "type": "weapon",
  "rarity": "legendary",
  "level_requirement": 15,
  "price": 10000,
  "stats": {
    "attack": 100,
    "crit_chance": 0.15
  },
  "equipment_slot": "weapon"
}
```

### Adding Quests (Optional)

1. Create `data/quests/` directory
2. Create `data/quests/my_quest.json`:

```json
{
  "id": "slay_dragon",
  "name": "Slay the Dragon",
  "type": "kill",
  "objectives": [
    {
      "type": "kill",
      "target": "dragon",
      "amount": 1,
      "description": "Defeat the Ancient Dragon"
    }
  ],
  "rewards": {
    "gold": 5000,
    "exp": 1000,
    "items": [
      {
        "item_id": "dragon_scale",
        "quantity": 3
      }
    ]
  }
}
```

## Bot Commands

Default commands available in the bot:

- `/start` - Initialize player
- `/profile` - View player stats
- `/fight` - Start combat
- `/inventory` - View inventory
- `/shop` - Browse shop
- `/quests` - View active quests (if quest system enabled)

## Extending the Bot

### Adding Custom Commands

Edit `bot.py` and add new handlers:

```python
@bot.message_handler(commands=['mycommand'])
async def my_command_handler(message):
    # Your custom logic here
    pass
```

### Adding Custom Modules

Create your own modules in a `modules/` directory:

```python
# modules/my_module.py
from engine.core.events import event_bus

class MyModule:
    def __init__(self, state):
        self.state = state
        event_bus.subscribe("some_event", self.handle_event)
    
    def handle_event(self, event):
        # Your custom logic
        pass
```

## Troubleshooting

### Bot doesn't respond

1. Check that bot token is correct in `.env`
2. Check console for error messages
3. Verify bot is not already running in another terminal

### Data validation errors

1. Check that JSON files are valid (use a JSON validator)
2. Verify all required fields are present (see schemas)
3. Check that IDs are unique and match pattern `^[a-z0-9_]+$`

### Import errors

1. Make sure engine is installed: `pip install -e ../../`
2. Verify virtual environment is activated
3. Check that all requirements are installed

## Next Steps

1. ✅ Customize content (mobs, items)
2. ✅ Test bot with /start command
3. ✅ Add more game content
4. ✅ Implement custom commands
5. ✅ Balance game economy
6. ✅ Deploy to production

## Resources

- [Engine Documentation](../../docs/API_REFERENCE.md)
- [Technical Documentation](../../docs/TECHNICAL_DOCUMENTATION.md)
- [Quick Start Guide](../../docs/QUICKSTART.md)

## License

This template is part of the Telegram Game Engine project.
See main project for license information.

