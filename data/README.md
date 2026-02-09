# Test Fixtures Data

This directory contains test data used by pytest test suite.

⚠️ **DO NOT DELETE** - Required for tests to pass.

## Structure

```
data/
├── schemas/       # JSON schemas for validation (copied from templates/rpg)
├── mobs/          # Test mob data
└── items/         # Test item data
```

## Purpose

These files are fixtures used by:
- `tests/test_spawning.py` - Tests for SpawnMobCommand and SpawnItemCommand
- `tests/test_data_loader.py` - Tests for DataLoader
- `tests/test_modules.py` - Tests for game modules

## Content

The test data includes:
- **Mobs:** goblin_warrior, orc_chieftain, dragon_ancient
- **Items:** health_potion, health_potion_small, iron_sword, rusty_sword, legendary_sword, gold_coin

## Note

This is NOT the same as `templates/` which contain starter templates for new games.
This data is specifically for testing purposes only.

