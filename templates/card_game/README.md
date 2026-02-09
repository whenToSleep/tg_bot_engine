# Card Game Template for Telegram Bot Engine

This template provides a ready-to-use structure for creating a card battle game bot on Telegram.

## Features

✨ **Included Systems:**
- 🃏 Card collection system
- 🎴 Deck building
- ⚔️ Turn-based card battles
- 💎 Mana system
- 📊 Card effects and keywords
- ⭐ Rarity tiers

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
cd templates/card_game
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
rm data/cards/_example_*.json

# Create your own cards
```

### 4. Run Bot

```bash
python bot.py
```

## Project Structure

```
templates/card_game/
├── data/
│   ├── schemas/       # Validation schemas
│   └── cards/         # Card definitions
├── bot.py             # Main bot file
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Card Types

### Minions

Creatures that can attack and defend:

```json
{
  "id": "knight",
  "name": "Knight",
  "cost": 4,
  "type": "minion",
  "attack": 4,
  "health": 5,
  "keywords": ["taunt"]
}
```

### Spells

One-time effects:

```json
{
  "id": "heal",
  "name": "Healing Touch",
  "cost": 3,
  "type": "spell",
  "effects": [
    {
      "type": "heal",
      "target": "ally",
      "value": 8
    }
  ]
}
```

### Weapons

Equipment for your hero:

```json
{
  "id": "sword",
  "name": "Steel Sword",
  "cost": 3,
  "type": "weapon",
  "attack": 3,
  "durability": 2
}
```

## Card Keywords

- **Charge** - Can attack immediately
- **Taunt** - Must be attacked first
- **Divine Shield** - Immune to first damage
- **Stealth** - Can't be targeted until attacks
- **Lifesteal** - Heal damage dealt
- **Windfury** - Can attack twice

## Bot Commands

- `/start` - Start playing
- `/collection` - View your cards
- `/deck` - Build/edit deck
- `/battle` - Start a battle
- `/shop` - Buy card packs
- `/stats` - View statistics

## Design Tips

1. **Balance mana costs** - Higher cost = more powerful
2. **Create synergies** - Cards that work well together
3. **Use keywords** - They add variety without complexity
4. **Test thoroughly** - Card interactions can be complex
5. **Rarity matters** - Legendary cards should feel special

## Example Card Set

Start with a basic set:
- 10 common minions (cost 1-4)
- 5 common spells
- 3 rare minions (cost 5-7)
- 2 rare spells
- 1 epic minion (cost 8+)
- 1 legendary card

## License

Part of the Telegram Game Engine project.

