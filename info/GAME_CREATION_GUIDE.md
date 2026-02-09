# 🎯 Руководство по созданию игр на Telegram Game Engine

## 📚 Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Создание первой игры](#создание-первой-игры)
3. [Базовые паттерны](#базовые-паттерны)
4. [Работа с модулями](#работа-с-модулями)
5. [Создание контента](#создание-контента)
6. [Интеграция с Telegram](#интеграция-с-telegram)
7. [Тестирование](#тестирование)
8. [Деплой](#деплой)
9. [Расширенные возможности](#расширенные-возможности)
10. [Частые вопросы](#частые-вопросы)

---

## Быстрый старт

### Установка

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить движок
pip install telegram-game-engine

# Создать новый проект
game-engine create my-rpg --template=rpg
cd my-rpg

# Запустить бота
python bot.py
```

### Структура проекта

```
my-rpg/
├── config.py              # Конфигурация (токен бота, БД)
├── bot.py                 # Точка входа
├── commands/              # Пользовательские команды
│   ├── __init__.py
│   └── custom_commands.py
├── data/                  # Игровой контент
│   ├── mobs/
│   │   ├── goblin.json
│   │   └── dragon.json
│   ├── items/
│   │   ├── sword.json
│   │   └── potion.json
│   └── skills/
│       └── fireball.json
├── modules/               # Пользовательские модули (если нужны)
│   └── custom_module.py
└── tests/                 # Тесты
    └── test_commands.py
```

### Минимальный config.py

```python
# config.py
import os

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///game.db")

# Модули игры
ENABLED_MODULES = [
    "engine.modules.combat",
    "engine.modules.economy",
    "engine.modules.inventory",
    "engine.modules.progression",
]

# Пути к данным
DATA_DIR = "data"
```

### Минимальный bot.py

```python
# bot.py
import asyncio
from engine import GameEngine
from engine.adapters.telegram import TelegramAdapter
from config import BOT_TOKEN, DATABASE_URL, ENABLED_MODULES, DATA_DIR

async def main():
    # Создать движок
    engine = GameEngine(
        database_url=DATABASE_URL,
        data_dir=DATA_DIR,
        modules=ENABLED_MODULES
    )
    
    # Инициализировать
    await engine.initialize()
    
    # Создать Telegram адаптер
    bot = TelegramAdapter(
        token=BOT_TOKEN,
        engine=engine
    )
    
    # Запустить
    print("🎮 Bot started!")
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Первый запуск

```bash
# Установить токен
export BOT_TOKEN="your_telegram_bot_token"

# Запустить
python bot.py

# Должно появиться
🎮 Bot started!
```

Готово! Бот работает с базовыми модулями.

---

## Создание первой игры

Создадим простую RPG: игрок бьёт мобов, получает золото, покупает улучшения.

### Шаг 1: Создать моба

```json
// data/mobs/slime.json
{
  "id": "slime",
  "name": "Slime",
  "hp": 30,
  "attack": 5,
  "defense": 2,
  "exp_reward": 10,
  "gold_reward": 5,
  "loot_table": [
    {
      "item_id": "slime_gel",
      "chance": 0.3,
      "quantity_min": 1,
      "quantity_max": 3
    }
  ],
  "abilities": []
}
```

### Шаг 2: Создать предмет

```json
// data/items/iron_sword.json
{
  "id": "iron_sword",
  "name": "Iron Sword",
  "type": "weapon",
  "description": "A sturdy iron sword",
  "price": 50,
  "stats": {
    "attack": 10
  },
  "requirements": {
    "level": 1
  }
}
```

### Шаг 3: Создать навык (опционально)

```json
// data/skills/power_strike.json
{
  "id": "power_strike",
  "name": "Power Strike",
  "type": "active",
  "cooldown": 3,
  "mana_cost": 10,
  "effects": [
    {
      "type": "damage",
      "base": 20,
      "stat_scaling": {
        "stat": "attack",
        "multiplier": 1.5
      }
    }
  ],
  "requirements": {
    "level": 5
  }
}
```

### Шаг 4: Настроить стартовое состояние игрока

```python
# commands/init_player.py
from engine.core.command import Command

class InitializePlayerCommand(Command):
    """Инициализация нового игрока"""
    
    def __init__(self, player_id: str, username: str):
        self.player_id = player_id
        self.username = username
    
    def get_entity_dependencies(self):
        return [self.player_id]
    
    def execute(self, state):
        # Проверить существует ли
        player = state.get_entity(self.player_id)
        if player:
            return {"existing": True}
        
        # Создать нового игрока
        new_player = {
            "_type": "player",
            "username": self.username,
            "level": 1,
            "exp": 0,
            "hp": 100,
            "max_hp": 100,
            "mana": 50,
            "max_mana": 50,
            "attack": 10,
            "defense": 5,
            "gold": 0,
            "inventory": ["wooden_sword"],  # Стартовое оружие
            "equipped": {
                "weapon": "wooden_sword"
            },
            "location": "town_square",
            "quests": []
        }
        
        state.set_entity(self.player_id, new_player)
        
        return {
            "existing": False,
            "player": new_player
        }
```

### Шаг 5: Создать команду боя

```python
# commands/battle.py
from engine.core.command import Command
from engine.core.events import event_bus, MobKilledEvent
from engine.data import data_loader
import random

class StartBattleCommand(Command):
    """Начать бой с мобом"""
    
    def __init__(self, player_id: str, mob_template_id: str):
        self.player_id = player_id
        self.mob_template_id = mob_template_id
        self.mob_id = f"mob_{player_id}_{random.randint(1000, 9999)}"
    
    def get_entity_dependencies(self):
        return [self.player_id, self.mob_id]
    
    def execute(self, state):
        player = state.get_entity(self.player_id)
        
        # Загрузить template моба
        mob_template = data_loader.get("mobs", self.mob_template_id)
        
        # Создать instance моба
        mob = {
            "_type": "mob",
            "template_id": self.mob_template_id,
            "hp": mob_template["hp"],
            "max_hp": mob_template["hp"],
            "attack": mob_template["attack"],
            "defense": mob_template["defense"]
        }
        
        state.set_entity(self.mob_id, mob)
        
        # Сохранить в состоянии игрока
        player["current_battle"] = self.mob_id
        state.set_entity(self.player_id, player)
        
        return {
            "mob_id": self.mob_id,
            "mob_name": mob_template["name"],
            "mob_hp": mob["hp"]
        }

class AttackCommand(Command):
    """Атаковать моба в бою"""
    
    def __init__(self, player_id: str):
        self.player_id = player_id
    
    def get_entity_dependencies(self):
        # Узнаем mob_id только при выполнении
        return [self.player_id]
    
    def execute(self, state):
        player = state.get_entity(self.player_id)
        
        # Проверить есть ли активный бой
        mob_id = player.get("current_battle")
        if not mob_id:
            raise ValueError("No active battle!")
        
        # Теперь блокируем моба (в реальности нужна двухфазная блокировка)
        mob = state.get_entity(mob_id)
        mob_template = data_loader.get("mobs", mob["template_id"])
        
        # Расчёт урона игрока
        player_damage = max(1, player["attack"] - mob["defense"])
        mob["hp"] -= player_damage
        
        result = {
            "player_damage": player_damage,
            "mob_hp": mob["hp"],
            "mob_killed": False
        }
        
        # Проверка убийства
        if mob["hp"] <= 0:
            # Награды
            player["exp"] += mob_template["exp_reward"]
            player["gold"] += mob_template["gold_reward"]
            
            # Лут
            loot = self._roll_loot(mob_template.get("loot_table", []))
            for item_id in loot:
                player["inventory"].append(item_id)
            
            # Очистить бой
            player["current_battle"] = None
            state.delete_entity(mob_id)
            
            result.update({
                "mob_killed": True,
                "exp_gained": mob_template["exp_reward"],
                "gold_gained": mob_template["gold_reward"],
                "loot": loot
            })
            
            # Событие убийства
            event_bus.publish(MobKilledEvent(
                player_id=self.player_id,
                mob_id=mob_id,
                mob_template=mob["template_id"]
            ))
        else:
            # Ответная атака моба
            mob_damage = max(1, mob["attack"] - player["defense"])
            player["hp"] -= mob_damage
            
            result["mob_damage"] = mob_damage
            result["player_hp"] = player["hp"]
            
            # Проверка смерти игрока
            if player["hp"] <= 0:
                result["player_died"] = True
                player["hp"] = 0
                player["current_battle"] = None
        
        state.set_entity(self.player_id, player)
        state.set_entity(mob_id, mob)
        
        return result
    
    def _roll_loot(self, loot_table):
        """Выдать лут по таблице"""
        loot = []
        for entry in loot_table:
            if random.random() < entry["chance"]:
                qty = random.randint(
                    entry["quantity_min"],
                    entry["quantity_max"]
                )
                for _ in range(qty):
                    loot.append(entry["item_id"])
        return loot
```

### Шаг 6: Интегрировать с Telegram

```python
# bot.py (расширенная версия)
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from commands.init_player import InitializePlayerCommand
from commands.battle import StartBattleCommand, AttackCommand

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message, engine):
    """Регистрация игрока"""
    player_id = str(message.from_user.id)
    username = message.from_user.username or "Unknown"
    
    cmd = InitializePlayerCommand(player_id, username)
    result = await engine.execute(cmd)
    
    if result.data["existing"]:
        await message.answer("С возвращением! 🎮")
    else:
        await message.answer(
            "🎉 Добро пожаловать в игру!\n\n"
            "Вы — начинающий герой в мире приключений.\n"
            "Используйте /fight чтобы сразиться с мобом!"
        )

@router.message(Command("fight"))
async def fight_handler(message: Message, engine):
    """Начать бой"""
    player_id = str(message.from_user.id)
    
    # Простой выбор моба (в реальности — по локации игрока)
    cmd = StartBattleCommand(player_id, "slime")
    result = await engine.execute(cmd)
    
    if not result.success:
        await message.answer(f"❌ {result.error}")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="⚔️ Атаковать",
            callback_data="attack"
        )]
    ])
    
    await message.answer(
        f"⚔️ Вы встретили {result.data['mob_name']}!\n"
        f"❤️ HP: {result.data['mob_hp']}",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "attack")
async def attack_callback(callback: CallbackQuery, engine):
    """Атака в бою"""
    player_id = str(callback.from_user.id)
    
    cmd = AttackCommand(player_id)
    result = await engine.execute(cmd)
    
    if not result.success:
        await callback.answer(f"❌ {result.error}", show_alert=True)
        return
    
    data = result.data
    text = f"⚔️ Вы нанесли {data['player_damage']} урона!\n"
    
    if data.get("mob_killed"):
        text += (
            f"\n💀 Моб убит!\n"
            f"✨ Опыт: +{data['exp_gained']}\n"
            f"💰 Золото: +{data['gold_gained']}"
        )
        if data.get("loot"):
            text += f"\n🎁 Лут: {', '.join(data['loot'])}"
        
        keyboard = None
    else:
        text += f"❤️ HP моба: {data['mob_hp']}\n\n"
        text += f"👹 Моб атакует! Урон: {data['mob_damage']}\n"
        text += f"❤️ Ваше HP: {data['player_hp']}"
        
        if data.get("player_died"):
            text += "\n\n💀 Вы погибли!"
            keyboard = None
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⚔️ Атаковать ещё",
                    callback_data="attack"
                )]
            ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# В main()
def create_bot():
    from aiogram import Bot, Dispatcher
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация роутера
    dp.include_router(router)
    
    # Middleware для передачи engine
    @dp.message.middleware()
    async def engine_middleware(handler, event, data):
        data["engine"] = engine
        return await handler(event, data)
    
    @dp.callback_query.middleware()
    async def engine_middleware_callback(handler, event, data):
        data["engine"] = engine
        return await handler(event, data)
    
    return dp, bot
```

### Шаг 7: Запуск

```bash
python bot.py
```

**Готово!** У вас работает RPG с:
- ✅ Регистрацией игроков
- ✅ Боями с мобами
- ✅ Прокачкой и лутом
- ✅ Экономикой (золото)

---

## Базовые паттерны

### Паттерн 1: Проверка ресурсов

```python
class BuyItemCommand(Command):
    def execute(self, state):
        player = state.get_entity(self.player_id)
        item_template = data_loader.get("items", self.item_id)
        
        # ❌ ПЛОХО
        if player["gold"] < item_template["price"]:
            return {"error": "Not enough gold"}
        
        # ✅ ХОРОШО
        if player["gold"] < item_template["price"]:
            raise ValueError("Not enough gold")
        
        # Логика покупки
        player["gold"] -= item_template["price"]
        player["inventory"].append(self.item_id)
        
        state.set_entity(self.player_id, player)
        
        return {
            "item_name": item_template["name"],
            "new_gold": player["gold"]
        }
```

**Почему:**
- Exception → rollback автоматически
- return {"error": ...} → commit произойдёт (неправильно)

### Паттерн 2: Валидация до изменения state

```python
class EquipItemCommand(Command):
    def execute(self, state):
        player = state.get_entity(self.player_id)
        item_template = data_loader.get("items", self.item_id)
        
        # ✅ Валидация ДО изменений
        if self.item_id not in player["inventory"]:
            raise ValueError("Item not in inventory")
        
        if player["level"] < item_template["requirements"]["level"]:
            raise ValueError("Level requirement not met")
        
        if item_template["type"] != "weapon":
            raise ValueError("Can only equip weapons")
        
        # ✅ Теперь безопасно изменять
        old_weapon = player["equipped"].get("weapon")
        player["equipped"]["weapon"] = self.item_id
        
        # Пересчитать статы
        player["attack"] = self._calculate_attack(player)
        
        state.set_entity(self.player_id, player)
        
        return {
            "equipped": self.item_id,
            "unequipped": old_weapon
        }
```

### Паттерн 3: Использование событий для декаплинга

```python
# ❌ ПЛОХО - прямая зависимость
class KillMobCommand(Command):
    def execute(self, state):
        # ... логика убийства
        
        # Прямой вызов другой логики
        self._check_achievements(player)
        self._update_quest_progress(player)
        self._trigger_special_event(player)
        # Команда знает про все системы!

# ✅ ХОРОШО - через события
class KillMobCommand(Command):
    def execute(self, state):
        # ... логика убийства
        
        # Просто публикуем событие
        event_bus.publish(MobKilledEvent(
            player_id=self.player_id,
            mob_template=mob["template_id"]
        ))
        
        # Команда не знает кто подписан!

# В модуле achievements
@subscribe("mob_killed")
def on_mob_killed(event):
    check_mob_kill_achievements(event.player_id)

# В модуле quests
@subscribe("mob_killed")
def on_mob_killed(event):
    update_quest_progress(event.player_id, "kill", event.mob_template)
```

### Паттерн 4: Композиция команд

```python
# ❌ ПЛОХО - одна огромная команда
class ComplexQuestCommand(Command):
    def execute(self, state):
        # 200 строк логики
        # Сложно тестировать
        # Сложно переиспользовать

# ✅ ХОРОШО - несколько маленьких
class AcceptQuestCommand(Command):
    def execute(self, state):
        # Только логика принятия квеста
        pass

class CompleteQuestCommand(Command):
    def execute(self, state):
        # Только логика завершения
        pass

class ClaimQuestRewardCommand(Command):
    def execute(self, state):
        # Только логика награды
        pass
```

### Паттерн 5: Фабрики для сложных объектов

```python
# factories/mob_factory.py
class MobFactory:
    """Фабрика для создания мобов"""
    
    @staticmethod
    def create(template_id: str, level: int = 1, modifiers: dict = None):
        """Создать instance моба"""
        template = data_loader.get("mobs", template_id)
        
        # Базовые статы
        mob = {
            "_type": "mob",
            "template_id": template_id,
            "level": level,
            "hp": template["hp"] * level,
            "max_hp": template["hp"] * level,
            "attack": template["attack"] + (level - 1) * 2,
            "defense": template["defense"] + (level - 1) * 1,
        }
        
        # Применить модификаторы (для событий, боссов)
        if modifiers:
            if "hp_multiplier" in modifiers:
                mob["hp"] *= modifiers["hp_multiplier"]
                mob["max_hp"] *= modifiers["hp_multiplier"]
            
            if "elite" in modifiers and modifiers["elite"]:
                mob["hp"] *= 2
                mob["attack"] *= 1.5
                mob["is_elite"] = True
        
        return mob

# Использование
mob = MobFactory.create("slime", level=5, modifiers={"elite": True})
```

---

## Работа с модулями

### Создание собственного модуля

```python
# modules/guild_module.py
from engine.core.module import GameModule
from engine.core.command import Command
from engine.core.events import event_bus

class CreateGuildCommand(Command):
    """Создать гильдию"""
    def __init__(self, player_id: str, guild_name: str):
        self.player_id = player_id
        self.guild_name = guild_name
        self.guild_id = f"guild_{guild_name.lower()}"
    
    def get_entity_dependencies(self):
        return [self.player_id, self.guild_id]
    
    def execute(self, state):
        player = state.get_entity(self.player_id)
        
        # Проверки
        if player.get("guild"):
            raise ValueError("Already in guild")
        
        if state.get_entity(self.guild_id):
            raise ValueError("Guild name taken")
        
        # Создать гильдию
        guild = {
            "_type": "guild",
            "name": self.guild_name,
            "leader": self.player_id,
            "members": [self.player_id],
            "level": 1,
            "treasury": 0,
            "created_at": datetime.now().isoformat()
        }
        
        state.set_entity(self.guild_id, guild)
        
        # Обновить игрока
        player["guild"] = self.guild_id
        state.set_entity(self.player_id, player)
        
        return {"guild_id": self.guild_id, "guild_name": self.guild_name}

class GuildModule(GameModule):
    """Модуль гильдий"""
    
    def register_commands(self, registry):
        """Зарегистрировать команды"""
        registry.add(CreateGuildCommand)
        registry.add(JoinGuildCommand)
        registry.add(LeaveGuildCommand)
        registry.add(DonateToGuildCommand)
    
    def register_events(self, bus):
        """Подписаться на события"""
        bus.subscribe("player_level_up", self.on_player_level_up)
    
    def on_player_level_up(self, event):
        """Начислить очки гильдии при levelup члена"""
        # Логика
        pass
    
    def register_data_types(self, loader):
        """Зарегистрировать схемы данных"""
        loader.add_schema("guild", {
            "type": "object",
            "required": ["name", "leader", "members"],
            "properties": {
                "name": {"type": "string"},
                "leader": {"type": "string"},
                "members": {"type": "array", "items": {"type": "string"}},
                "level": {"type": "integer", "minimum": 1}
            }
        })
```

### Подключение модуля

```python
# config.py
ENABLED_MODULES = [
    "engine.modules.combat",
    "engine.modules.economy",
    "modules.guild_module.GuildModule",  # Ваш модуль
]
```

---

## Создание контента

### JSON Schema для валидации

```python
# data/schemas/mob_schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "name", "hp", "attack", "defense", "exp_reward", "gold_reward"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-z_]+$",
      "description": "Уникальный ID моба"
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 50
    },
    "hp": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    },
    "attack": {
      "type": "integer",
      "minimum": 0
    },
    "defense": {
      "type": "integer",
      "minimum": 0
    },
    "exp_reward": {
      "type": "integer",
      "minimum": 0
    },
    "gold_reward": {
      "type": "integer",
      "minimum": 0
    },
    "abilities": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "chance"],
        "properties": {
          "id": {"type": "string"},
          "chance": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
          }
        }
      }
    },
    "loot_table": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["item_id", "chance", "quantity_min", "quantity_max"],
        "properties": {
          "item_id": {"type": "string"},
          "chance": {"type": "number", "minimum": 0, "maximum": 1},
          "quantity_min": {"type": "integer", "minimum": 1},
          "quantity_max": {"type": "integer", "minimum": 1}
        }
      }
    }
  }
}
```

### Горячая перезагрузка данных

```python
# admin_commands.py
from engine.data import data_loader

class ReloadDataCommand(Command):
    """Перезагрузить данные (только для админов!)"""
    
    def __init__(self, admin_id: str, data_type: str):
        self.admin_id = admin_id
        self.data_type = data_type
    
    def get_entity_dependencies(self):
        return []  # Не затрагивает сущности
    
    def execute(self, state):
        # Проверка прав (в реальности - через decorator)
        admin = state.get_entity(self.admin_id)
        if not admin.get("is_admin"):
            raise PermissionError("Not an admin")
        
        # Перезагрузка
        if self.data_type == "mobs":
            data_loader.reload("mobs")
        elif self.data_type == "items":
            data_loader.reload("items")
        elif self.data_type == "all":
            data_loader.reload_all()
        else:
            raise ValueError(f"Unknown data type: {self.data_type}")
        
        return {
            "reloaded": self.data_type,
            "count": len(data_loader.data[self.data_type])
        }
```

### Инструменты для контента

```python
# tools/validate_data.py
"""Валидация всех JSON файлов"""
import json
from pathlib import Path
from jsonschema import validate, ValidationError

def validate_all_mobs():
    schema_path = Path("data/schemas/mob_schema.json")
    with open(schema_path) as f:
        schema = json.load(f)
    
    mobs_dir = Path("data/mobs")
    errors = []
    
    for mob_file in mobs_dir.glob("*.json"):
        with open(mob_file) as f:
            try:
                mob_data = json.load(f)
                validate(instance=mob_data, schema=schema)
                print(f"✅ {mob_file.name}")
            except ValidationError as e:
                errors.append(f"❌ {mob_file.name}: {e.message}")
    
    if errors:
        print("\nErrors found:")
        for error in errors:
            print(error)
        return False
    
    print(f"\n✅ All {len(list(mobs_dir.glob('*.json')))} mobs valid!")
    return True

if __name__ == "__main__":
    validate_all_mobs()
```

---

## Интеграция с Telegram

### Продвинутые UI паттерны

```python
# ui/builders.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class InventoryUI:
    """Билдер для инвентаря"""
    
    @staticmethod
    def build(inventory: list, page: int = 0, items_per_page: int = 5):
        """Создать UI инвентаря с пагинацией"""
        start = page * items_per_page
        end = start + items_per_page
        page_items = inventory[start:end]
        
        keyboard = []
        
        # Кнопки предметов
        for item_id in page_items:
            item_template = data_loader.get("items", item_id)
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{item_template['name']}",
                    callback_data=f"item:{item_id}"
                )
            ])
        
        # Пагинация
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"inv:page:{page-1}"
            ))
        
        if end < len(inventory):
            nav_row.append(InlineKeyboardButton(
                text="Вперёд ➡️",
                callback_data=f"inv:page:{page+1}"
            ))
        
        if nav_row:
            keyboard.append(nav_row)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Использование
@router.message(Command("inventory"))
async def inventory_handler(message: Message, engine):
    player_id = str(message.from_user.id)
    player = await engine.get_entity(player_id)
    
    inventory = player.get("inventory", [])
    
    if not inventory:
        await message.answer("Ваш инвентарь пуст.")
        return
    
    keyboard = InventoryUI.build(inventory, page=0)
    await message.answer(
        f"🎒 Инвентарь ({len(inventory)} предметов):",
        reply_markup=keyboard
    )
```

### State-машина для сложных диалогов

```python
# Для сложных квестов, торговли, создания персонажа
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class TradeStates(StatesGroup):
    selecting_item = State()
    entering_price = State()
    confirming = State()

@router.message(Command("sell"))
async def start_selling(message: Message, state: FSMContext):
    """Начать продажу предмета"""
    await state.set_state(TradeStates.selecting_item)
    await message.answer(
        "Выберите предмет для продажи:",
        reply_markup=build_inventory_keyboard()
    )

@router.callback_query(TradeStates.selecting_item, F.data.startswith("item:"))
async def item_selected(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split(":")[1]
    await state.update_data(item_id=item_id)
    await state.set_state(TradeStates.entering_price)
    
    await callback.message.answer("Введите цену:")

@router.message(TradeStates.entering_price)
async def price_entered(message: Message, state: FSMContext, engine):
    try:
        price = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    item_id = data["item_id"]
    
    # Выполнить команду продажи
    cmd = SellItemCommand(
        player_id=str(message.from_user.id),
        item_id=item_id,
        price=price
    )
    
    result = await engine.execute(cmd)
    
    if result.success:
        await message.answer(f"✅ Предмет выставлен на продажу за {price} золота!")
        await state.clear()
    else:
        await message.answer(f"❌ {result.error}")
```

---

## Тестирование

### Unit тесты команд

```python
# tests/test_battle.py
import pytest
from commands.battle import AttackCommand, StartBattleCommand
from engine.core.state import GameState
from engine.data import data_loader

@pytest.fixture
def game_state():
    """Создать тестовое состояние"""
    state = GameState()
    
    # Игрок
    state.set_entity("player_1", {
        "_type": "player",
        "hp": 100,
        "max_hp": 100,
        "attack": 20,
        "defense": 5,
        "gold": 0,
        "exp": 0
    })
    
    return state

def test_start_battle(game_state):
    """Тест начала боя"""
    cmd = StartBattleCommand("player_1", "slime")
    result = cmd.execute(game_state)
    
    assert result["mob_name"] == "Slime"
    assert result["mob_hp"] == 30
    
    # Проверить что моб создан
    mob = game_state.get_entity(result["mob_id"])
    assert mob is not None
    assert mob["hp"] == 30

def test_attack_kills_mob(game_state):
    """Тест убийства моба"""
    # Создать боссая
    start_cmd = StartBattleCommand("player_1", "slime")
    start_result = start_cmd.execute(game_state)
    
    player = game_state.get_entity("player_1")
    player["current_battle"] = start_result["mob_id"]
    game_state.set_entity("player_1", player)
    
    # Атаковать (должно убить с одного удара при attack=20)
    attack_cmd = AttackCommand("player_1")
    attack_result = attack_cmd.execute(game_state)
    
    assert attack_result["mob_killed"] == True
    assert attack_result["exp_gained"] == 10
    assert attack_result["gold_gained"] == 5
    
    # Проверить награды применены
    player = game_state.get_entity("player_1")
    assert player["exp"] == 10
    assert player["gold"] == 5
    assert player["current_battle"] is None

def test_attack_without_battle_fails(game_state):
    """Тест атаки без активного боя"""
    cmd = AttackCommand("player_1")
    
    with pytest.raises(ValueError, match="No active battle"):
        cmd.execute(game_state)
```

### Integration тесты

```python
# tests/test_integration.py
import pytest
import asyncio
from engine import GameEngine

@pytest.mark.asyncio
async def test_full_battle_flow():
    """Тест полного flow боя"""
    # Создать движок
    engine = GameEngine(
        database_url="sqlite:///:memory:",
        data_dir="data"
    )
    
    await engine.initialize()
    
    # Создать игрока
    from commands.init_player import InitializePlayerCommand
    init_cmd = InitializePlayerCommand("test_player", "TestUser")
    result = await engine.execute(init_cmd)
    assert result.success
    
    # Начать бой
    from commands.battle import StartBattleCommand
    battle_cmd = StartBattleCommand("test_player", "slime")
    result = await engine.execute(battle_cmd)
    assert result.success
    
    # Атаковать до победы
    from commands.battle import AttackCommand
    max_attacks = 10
    for i in range(max_attacks):
        attack_cmd = AttackCommand("test_player")
        result = await engine.execute(attack_cmd)
        assert result.success
        
        if result.data.get("mob_killed"):
            break
    
    # Проверить что получили награду
    player = await engine.get_entity("test_player")
    assert player["exp"] > 0
    assert player["gold"] > 0
```

### Load тесты

```python
# tests/test_load.py
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_battles():
    """Тест 100 параллельных боёв"""
    engine = GameEngine(...)
    await engine.initialize()
    
    # Создать 100 игроков
    players = []
    for i in range(100):
        player_id = f"player_{i}"
        cmd = InitializePlayerCommand(player_id, f"User{i}")
        await engine.execute(cmd)
        players.append(player_id)
    
    # Запустить 100 боёв одновременно
    async def battle(player_id):
        start = StartBattleCommand(player_id, "slime")
        await engine.execute(start)
        
        for _ in range(5):
            attack = AttackCommand(player_id)
            result = await engine.execute(attack)
            if result.data.get("mob_killed"):
                break
    
    # Измерить время
    import time
    start_time = time.time()
    
    await asyncio.gather(*[battle(p) for p in players])
    
    duration = time.time() - start_time
    
    print(f"100 concurrent battles in {duration:.2f}s")
    assert duration < 10  # Должно быть быстрее 10 секунд
```

---

## Деплой

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установить зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать код
COPY . .

# Запустить
CMD ["python", "bot.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DATABASE_URL=postgresql://postgres:password@db:5432/gamedb
    depends_on:
      - db
    restart: unless-stopped
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=gamedb
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Production конфигурация

```python
# config_prod.py
import os

# Telegram
BOT_TOKEN = os.environ["BOT_TOKEN"]

# Database
DATABASE_URL = os.environ["DATABASE_URL"]

# Redis для кеширования
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Мониторинг
SENTRY_DSN = os.getenv("SENTRY_DSN")

# Логирование
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": ["console", "file"]
}

# Rate limiting
RATE_LIMITS = {
    "commands_per_user_per_minute": 20,
    "commands_per_user_per_hour": 500
}
```

---

## Расширенные возможности

### Scheduled команды (для Idle игр)

```python
# scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from commands.idle import CollectIdleResourcesCommand

class GameScheduler:
    def __init__(self, engine):
        self.engine = engine
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Запустить задачи"""
        # Каждую минуту собирать idle ресурсы
        self.scheduler.add_job(
            self.collect_idle_resources,
            'interval',
            minutes=1
        )
        
        # Каждый день в полночь сбросить daily квесты
        self.scheduler.add_job(
            self.reset_daily_quests,
            'cron',
            hour=0, minute=0
        )
        
        self.scheduler.start()
    
    async def collect_idle_resources(self):
        """Собрать ресурсы для всех idle игроков"""
        # Получить активных игроков
        active_players = await self.get_active_players()
        
        for player_id in active_players:
            cmd = CollectIdleResourcesCommand(player_id)
            await self.engine.execute(cmd)
```

### Analytics

```python
# analytics.py
from engine.core.events import event_bus
import logging

analytics_logger = logging.getLogger("analytics")

@event_bus.subscribe("command_executed")
def track_command(event):
    """Трекинг всех команд"""
    analytics_logger.info({
        "event": "command",
        "command_type": event.command_type,
        "player_id": event.player_id,
        "success": event.success,
        "duration_ms": event.duration
    })

@event_bus.subscribe("player_level_up")
def track_levelup(event):
    """Трекинг levelup"""
    analytics_logger.info({
        "event": "level_up",
        "player_id": event.player_id,
        "new_level": event.new_level,
        "play_time_hours": event.play_time / 3600
    })
```

### Admin панель

```python
# admin/dashboard.py
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/admin/stats")
async def get_stats(engine: GameEngine = Depends()):
    """Статистика игры"""
    total_players = await engine.count_entities("player")
    active_today = await engine.count_active_players(hours=24)
    
    return {
        "total_players": total_players,
        "active_today": active_today,
        "top_level": await engine.get_top_players("level", limit=10)
    }

@app.post("/admin/broadcast")
async def broadcast_message(message: str, bot: TelegramBot = Depends()):
    """Рассылка всем игрокам"""
    players = await engine.get_all_players()
    
    for player in players:
        try:
            await bot.send_message(player["_id"], message)
        except Exception as e:
            logging.error(f"Failed to send to {player['_id']}: {e}")
    
    return {"sent": len(players)}
```

---

## Частые вопросы

### Q: Как делать PvP?

```python
class DuelCommand(Command):
    """PvP дуэль"""
    def __init__(self, attacker_id: str, defender_id: str):
        self.attacker_id = attacker_id
        self.defender_id = defender_id
    
    def get_entity_dependencies(self):
        # Блокируем обоих игроков
        # В отсортированном порядке (предотвращает deadlock)
        return sorted([self.attacker_id, self.defender_id])
    
    def execute(self, state):
        attacker = state.get_entity(self.attacker_id)
        defender = state.get_entity(self.defender_id)
        
        # Проверки
        if attacker.get("in_duel") or defender.get("in_duel"):
            raise ValueError("Already in duel")
        
        # Расчёт боя
        # ...
        
        return result
```

### Q: Как делать гильдии/кланы?

Создайте сущность "guild" и храните список участников. Команды гильдии блокируют guild entity.

### Q: Как делать аукцион/маркет?

Создайте сущность "auction" для каждого лота. При покупке блокируйте аукцион + покупателя.

### Q: Как делать рейтинги?

Используйте отдельную таблицу/коллекцию для рейтинга. Обновляйте через события.

### Q: Как оптимизировать производительность?

1. Connection pooling для БД
2. Кеширование статических данных (templates)
3. Lazy loading игроков
4. Батчинг операций
5. Индексы в БД

---

## Итоги

Теперь вы знаете:

✅ Как установить движок  
✅ Как создать первую игру  
✅ Базовые паттерны разработки  
✅ Как работать с модулями  
✅ Как создавать контент  
✅ Как интегрироваться с Telegram  
✅ Как тестировать  
✅ Как деплоить

### Следующие шаги

1. Прочитайте [API Reference](API_REFERENCE.md)
2. Изучите [Examples](../examples/)
3. Присоединитесь к [Community](COMMUNITY.md)

Удачи в разработке! 🚀
