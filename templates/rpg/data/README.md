# RPG Game Data

This directory contains all game content for your RPG.

## Structure

```
data/
├── schemas/       # JSON schemas for validation
├── mobs/          # Enemy definitions
├── items/         # Item definitions
├── quests/        # Quest definitions (optional)
└── locations/     # Location definitions (optional)
```

## Getting Started

### 1. Remove Example Files

Delete all files starting with `_example_`:
```bash
rm mobs/_example_*.json
rm items/_example_*.json
```

### 2. Create Your Content

#### Creating a Mob

Create a new file in `mobs/` folder (e.g., `skeleton.json`):

```json
{
  "id": "skeleton_warrior",
  "name": "Skeleton Warrior",
  "description": "An undead warrior risen from the grave",
  "hp": 80,
  "attack": 12,
  "defense": 5,
  "gold_reward": 50,
  "experience_reward": 30,
  "level": 3,
  "tags": ["undead", "warrior"]
}
```

#### Creating an Item

Create a new file in `items/` folder (e.g., `steel_sword.json`):

```json
{
  "id": "steel_sword",
  "name": "Steel Sword",
  "description": "A well-crafted steel blade",
  "type": "weapon",
  "rarity": "uncommon",
  "level_requirement": 5,
  "price": 500,
  "stats": {
    "attack": 20,
    "crit_chance": 0.05
  },
  "equipment_slot": "weapon"
}
```

## Validation

All JSON files are validated against schemas in `schemas/` directory.

Use JSON Schema validators in your editor for auto-completion and validation:
- VSCode: Install "JSON Schema" extension
- Use `$schema` property in your JSON files

## Tips

1. **IDs must be unique** - Use descriptive snake_case names
2. **Balance carefully** - Test mob difficulty vs player power
3. **Start simple** - Create 3-5 mobs and items first
4. **Use tags** - They help with categorization and quests
5. **Check schemas** - Look at schema files for all available properties

## Questions?

See the main [templates guide](../../README.md) for more information.

