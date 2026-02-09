# Idle Clicker Template for Telegram Bot Engine

This template provides a ready-to-use structure for creating an idle/incremental game bot on Telegram.

## Features

✨ **Included Systems:**
- 🏭 Building system with auto-production
- ⬆️ Upgrade system
- 💰 Resource accumulation
- 📊 Progress tracking
- 🔄 Prestige mechanics (optional)

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
cd templates/idle_clicker
pip install -r requirements.txt
```

### 2. Configure Bot

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your bot token
```

### 3. Customize Content

Remove example files and create your own:

```bash
# Remove examples
rm data/buildings/_example_*.json
rm data/upgrades/_example_*.json

# Create your own buildings and upgrades
```

### 4. Run Bot

```bash
python bot.py
```

## Project Structure

```
templates/idle_clicker/
├── data/
│   ├── schemas/       # Validation schemas
│   ├── buildings/     # Building definitions
│   └── upgrades/      # Upgrade definitions
├── bot.py             # Main bot file
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Game Mechanics

### Buildings

Buildings generate resources automatically over time:

```json
{
  "id": "mine",
  "name": "Gold Mine",
  "base_cost": 50,
  "production_rate": 2.0,
  "category": "production",
  "icon": "⛏️"
}
```

Cost formula: `base_cost * (cost_multiplier ^ current_level)`
Production formula: `production_rate * (production_multiplier ^ current_level)`

### Upgrades

Upgrades provide permanent bonuses:

```json
{
  "id": "better_tools",
  "name": "Better Tools",
  "cost": 500,
  "effect": {
    "type": "multiply_production",
    "target": "mine",
    "value": 2.0
  }
}
```

Effect types:
- `multiply_production` - Multiply building production
- `multiply_click` - Multiply manual click value
- `unlock_building` - Unlock new building
- `auto_click` - Enable auto-clicking
- `reduce_cost` - Reduce building costs

## Bot Commands

- `/start` - Start playing
- `/balance` - Check resources
- `/buildings` - View and buy buildings
- `/upgrades` - View and buy upgrades
- `/stats` - View statistics
- `/prestige` - Reset for bonuses (optional)

## Customization Tips

1. **Balance production rates** - Start slow, scale exponentially
2. **Price upgrades carefully** - Should cost ~10x current production
3. **Add variety** - Different building types keep it interesting
4. **Implement milestones** - Achievements for reaching goals
5. **Consider prestige** - Let players reset for permanent bonuses

## License

Part of the Telegram Game Engine project.

