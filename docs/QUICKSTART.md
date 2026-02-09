# 🚀 QuickStart — Создание игры за 30 минут

Пошаговое руководство по созданию простой RPG игры на Telegram Game Engine.

---

## 🎯 Что мы создадим

Простую текстовую RPG, где игрок может:
- ⚔️ Сражаться с мобами
- 💰 Получать золото и опыт
- 📈 Повышать уровень
- 🛒 Покупать предметы

---

## 📋 Требования

- **Python 3.9+** — проверьте: `python --version`
- **Telegram Bot Token** — получите у [@BotFather](https://t.me/BotFather)
- **5-10 минут** — на настройку

---

## ⚡ Вариант 1: Использовать готовый шаблон (рекомендуется)

### Самый быстрый способ начать:

```bash
# 1. Скопировать шаблон
cp -r templates/rpg my_rpg_game
cd my_rpg_game

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Установить зависимости
pip install -e path/to/tg_bot_engine
pip install -r requirements.txt

# 4. Настроить токен
cp .env.example .env
# Откройте .env и добавьте: TELEGRAM_BOT_TOKEN=your_token

# 5. Запустить
python bot.py
```

**✅ Готово!** Бот запущен и готов к игре.

📖 Подробнее о шаблонах: см. README.md в каждой папке `templates/`

---

## 🔧 Вариант 2: Создать с нуля

### Шаг 1: Подготовка окружения

```bash
# Создать проект
mkdir my_rpg_game
cd my_rpg_game

# Создать виртуальное окружение
python -m venv venv

# Активировать
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Установить движок
pip install -e path/to/tg_bot_engine

# Установить зависимости
pip install aiogram>=3.3.0 python-dotenv>=1.0.0
```

### Шаг 2: Создать структуру

```bash
# Создать директории
mkdir data data/mobs data/items data/schemas

# Создать файлы
touch bot.py config.py .env requirements.txt
```

**Структура проекта:**
```
my_rpg_game/
├── data/
│   ├── schemas/
│   │   ├── mob_schema.json
│   │   └── item_schema.json
│   ├── mobs/
│   │   └── goblin.json
│   └── items/
│       └── health_potion.json
├── bot.py
├── config.py
├── .env
└── requirements.txt
```

### Шаг 3: Создать схемы данных

**`data/schemas/mob_schema.json`**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "hp", "attack", "gold_reward", "exp_reward"],
  "properties": {
    "name": {"type": "string"},
    "hp": {"type": "integer", "minimum": 1},
    "attack": {"type": "integer", "minimum": 1},
    "gold_reward": {"type": "integer", "minimum": 0},
    "exp_reward": {"type": "integer", "minimum": 0},
    "description": {"type": "string"}
  }
}
```

**`data/schemas/item_schema.json`**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "type", "price"],
  "properties": {
    "name": {"type": "string"},
    "type": {
      "type": "string",
      "enum": ["weapon", "armor", "consumable"]
    },
    "price": {"type": "integer", "minimum": 0},
    "description": {"type": "string"},
    "effect": {"type": "object"}
  }
}
```

### Шаг 4: Создать игровой контент

**`data/mobs/goblin.json`**
```json
{
  "name": "Гоблин",
  "hp": 30,
  "attack": 5,
  "gold_reward": 10,
  "exp_reward": 15,
  "description": "Маленький зелёный гоблин с дубинкой"
}
```

**`data/mobs/orc.json`**
```json
{
  "name": "Орк",
  "hp": 60,
  "attack": 10,
  "gold_reward": 25,
  "exp_reward": 30,
  "description": "Свирепый орк-воин"
}
```

**`data/items/health_potion.json`**
```json
{
  "name": "Зелье здоровья",
  "type": "consumable",
  "price": 20,
  "description": "Восстанавливает 50 HP",
  "effect": {"heal": 50}
}
```

### Шаг 5: Конфигурация

**`config.py`**
```python
import os

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Database
DATABASE_PATH = "game.db"

# Data
DATA_DIR = "data"

# Game balance
INITIAL_GOLD = 50
INITIAL_HP = 100
INITIAL_ATTACK = 10
```

**`.env`**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

**`requirements.txt`**
```txt
aiogram>=3.3.0
python-dotenv>=1.0.0
```

### Шаг 6: Создать бота

**`bot.py`**
```python
import asyncio
import logging
import os
from dotenv import load_dotenv

from config import DATABASE_PATH, DATA_DIR
from engine import (
    PersistentGameState,
    AsyncCommandExecutor,
    SQLiteRepository,
    get_global_loader,
    get_event_bus,
    GameBot,
    ProgressionModule,
)

# Загрузить .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Запуск бота."""
    
    # Получить токен
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        logger.info("💡 Добавьте токен в файл .env")
        return
    
    logger.info("🎮 Запуск игрового бота...")
    
    # 1. Инициализация хранилища
    logger.info("📦 Инициализация базы данных...")
    repo = SQLiteRepository(DATABASE_PATH)
    state = PersistentGameState(repo, auto_flush=True)
    executor = AsyncCommandExecutor(state)
    
    # 2. Загрузка игровых данных
    logger.info("📚 Загрузка игрового контента...")
    loader = get_global_loader()
    loader.set_data_directory(DATA_DIR)
    
    try:
        loader.load_category("mobs", "mob_schema.json")
        loader.load_category("items", "item_schema.json")
        stats = loader.get_stats()
        logger.info(f"✅ Загружено: {stats}")
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки данных: {e}")
        return
    
    # 3. Инициализация игровых модулей
    logger.info("🎯 Инициализация игровых модулей...")
    event_bus = get_event_bus()
    progression = ProgressionModule(state, event_bus)
    
    # 4. Создание и запуск бота
    logger.info("🤖 Запуск Telegram бота...")
    bot = GameBot(
        token=token,
        state=state,
        executor=executor
    )
    
    logger.info("=" * 60)
    logger.info("✅ Бот успешно запущен!")
    logger.info("=" * 60)
    logger.info("📱 Найдите бота в Telegram и отправьте /start")
    logger.info("⏹️  Нажмите Ctrl+C для остановки")
    logger.info("=" * 60)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("\n🛑 Остановка бота...")
    finally:
        await bot.stop()
        logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
```

### Шаг 7: Запустить

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить бота
python bot.py
```

### Шаг 8: Протестировать

Откройте бота в Telegram:

1. `/start` — начать игру
2. `/profile` — посмотреть статистику
3. `/fight` — сразиться с мобом
4. `/claim_daily` — получить награду

---

## 🎨 Кастомизация

### Добавить свою команду

**`commands/heal.py`**
```python
from engine import Command, GameState
from typing import List

class HealCommand(Command):
    """Команда лечения игрока."""
    
    def __init__(self, player_id: str, amount: int):
        self.player_id = player_id
        self.amount = amount
    
    def get_entity_dependencies(self) -> List[str]:
        return [self.player_id]
    
    def execute(self, state: GameState) -> dict:
        player = state.get_entity(self.player_id)
        if not player:
            raise ValueError(f"Player {self.player_id} not found")
        
        old_hp = player.get("hp", 100)
        max_hp = player.get("max_hp", 100)
        new_hp = min(old_hp + self.amount, max_hp)
        
        player["hp"] = new_hp
        state.set_entity(self.player_id, player)
        
        return {
            "old_hp": old_hp,
            "new_hp": new_hp,
            "healed": new_hp - old_hp
        }
```

### Расширить бота

```python
from aiogram import types
from aiogram.filters import Command as TgCommand
from engine import GameBot
from commands.heal import HealCommand

class MyGameBot(GameBot):
    """Расширенный бот."""
    
    def _register_handlers(self):
        super()._register_handlers()
        
        @self.dp.message(TgCommand("heal"))
        async def heal_handler(message: types.Message):
            user_id = str(message.from_user.id)
            
            result = await self.executor.execute(
                HealCommand(user_id, 50)
            )
            
            if result.success:
                await message.answer(
                    f"❤️ +{result.data['healed']} HP\n"
                    f"Текущее HP: {result.data['new_hp']}"
                )
            else:
                await message.answer(f"❌ {result.error}")

# Использовать
bot = MyGameBot(token=token, state=state, executor=executor)
```

---

## 📚 Следующие шаги

### Изучить документацию

- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** — полная техническая документация
- **[API_REFERENCE.md](API_REFERENCE.md)** — справочник по API
- **Папка `templates/`** — готовые шаблоны игр (RPG, Idle, Card Game)

### Добавить механики

- **Достижения** — используйте `AchievementModule`
- **Квесты** — создайте свой `QuestModule`
- **PvP** — используйте `MatchmakingService`
- **Gacha** — используйте `GachaService`

### Расширить контент

1. Добавьте больше мобов в `data/mobs/`
2. Добавьте больше предметов в `data/items/`
3. Создайте локации, квесты, боссов
4. Настройте баланс игры

---

## 🐛 Отладка

### Проверить данные

```python
from engine import get_global_loader

loader = get_global_loader()
loader.load_category("mobs", "mob_schema.json")

all_mobs = loader.get_all("mobs")
for mob_id, mob in all_mobs.items():
    print(f"{mob_id}: {mob['name']} (HP: {mob['hp']})")
```

### Посмотреть игрока

```python
player = state.get_entity("player_123")
print(f"Gold: {player.get('gold', 0)}")
print(f"Level: {player.get('level', 1)}")
```

### Включить DEBUG

```python
logging.basicConfig(level=logging.DEBUG)
```

---



