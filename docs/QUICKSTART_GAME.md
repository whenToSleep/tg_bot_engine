# 🎮 Создание игры за 30 минут

Пошаговое руководство по созданию простой RPG игры на Telegram Game Engine с нуля.

## 🎯 Что мы создадим

Простую текстовую RPG где игрок может:
- Сражаться с мобами
- Получать золото и опыт
- Повышать уровень
- Покупать предметы

## 📋 Предварительные требования

- **Python 3.9+** - Проверьте версию: `python --version`
- **Telegram Bot Token** - Получите у @BotFather
- **Telegram Game Engine** - Установлен (см. ниже)

## 🔧 Шаг 0: Подготовка окружения

**⚠️ ВАЖНО:** Всегда используйте виртуальное окружение для изоляции зависимостей!

```bash
# 1. Создать директорию проекта
mkdir my_rpg_game
cd my_rpg_game

# 2. Создать виртуальное окружение
python -m venv venv

# 3. Активировать виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Обновить pip
pip install --upgrade pip

# 5. Установить движок (из родительского проекта)
pip install -e path/to/tg_bot_engine ("A:\my_work_project\tg_bot_engine")

# Или если движок опубликован на PyPI:
# pip install tg-bot-engine

# 6. Установить aiogram для Telegram
pip install aiogram>=3.3.0 python-dotenv>=1.0.0
```

**💡 Tip:** Для быстрого старта используйте готовые [шаблоны](TEMPLATES_GUIDE.md)!

## 🚀 Шаг 1: Создать структуру проекта

```bash
mkdir my_rpg
cd my_rpg

# Создать директории
mkdir data
mkdir data/mobs
mkdir data/items
mkdir data/schemas
```

Структура проекта:
```
my_rpg/
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
└── requirements.txt
```

## 📝 Шаг 2: Создать схемы данных

### `data/schemas/mob_schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "hp", "attack", "gold_reward", "exp_reward"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Отображаемое имя моба"
    },
    "hp": {
      "type": "integer",
      "minimum": 1,
      "description": "Очки здоровья"
    },
    "attack": {
      "type": "integer",
      "minimum": 1,
      "description": "Урон за атаку"
    },
    "gold_reward": {
      "type": "integer",
      "minimum": 0,
      "description": "Золото за убийство"
    },
    "exp_reward": {
      "type": "integer",
      "minimum": 0,
      "description": "Опыт за убийство"
    },
    "description": {
      "type": "string",
      "description": "Описание моба"
    }
  }
}
```

### `data/schemas/item_schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "type", "price"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Название предмета"
    },
    "type": {
      "type": "string",
      "enum": ["weapon", "armor", "consumable"],
      "description": "Тип предмета"
    },
    "price": {
      "type": "integer",
      "minimum": 0,
      "description": "Цена в магазине"
    },
    "description": {
      "type": "string"
    },
    "effect": {
      "type": "object",
      "description": "Эффект предмета"
    }
  }
}
```

## 🐉 Шаг 3: Создать игровой контент

### `data/mobs/goblin.json`

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

### `data/mobs/orc.json`

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

### `data/items/health_potion.json`

```json
{
  "name": "Зелье здоровья",
  "type": "consumable",
  "price": 20,
  "description": "Восстанавливает 50 HP",
  "effect": {
    "heal": 50
  }
}
```

### `data/items/iron_sword.json`

```json
{
  "name": "Железный меч",
  "type": "weapon",
  "price": 100,
  "description": "Прочный железный меч",
  "effect": {
    "attack_bonus": 5
  }
}
```

## ⚙️ Шаг 4: Конфигурация

### `config.py`

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
BASE_EXP_TO_LEVEL = 100
```

### `requirements.txt`

```txt
aiogram>=3.3.0
tg-bot-engine>=0.5.5
```

## 🤖 Шаг 5: Создать бота

### `bot.py`

```python
import asyncio
import logging
import os
from config import (
    TELEGRAM_BOT_TOKEN,
    DATABASE_PATH,
    DATA_DIR,
    INITIAL_GOLD,
    INITIAL_HP,
    INITIAL_ATTACK
)

from engine import (
    PersistentGameState,
    AsyncCommandExecutor,
    SQLiteRepository,
    get_global_loader,
    get_event_bus,
    GameBot,
    ProgressionModule,
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Запуск бота."""
    
    # Проверить токен
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        logger.info("Установите: export TELEGRAM_BOT_TOKEN='your_token'")
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
        token=TELEGRAM_BOT_TOKEN,
        state=state,
        executor=executor
    )
    
    logger.info("=" * 60)
    logger.info("✅ Бот успешно запущен!")
    logger.info("=" * 60)
    logger.info("📱 Найдите вашего бота в Telegram и отправьте /start")
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

## 🚀 Шаг 6: Запустить бота

```bash
# Установить токен бота
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Установить зависимости
pip install -r requirements.txt

# Запустить бота
python bot.py
```

## 🎮 Шаг 7: Протестировать в Telegram

Откройте вашего бота в Telegram и попробуйте команды:

1. `/start` - начать игру
2. `/profile` - посмотреть статистику
3. `/fight` - сразиться с мобом
4. `/claim_daily` - получить ежедневную награду

## 🎨 Шаг 8: Кастомизация (опционально)

### Добавить пользовательскую команду

Создайте `commands/heal.py`:

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
        
        # Вылечить игрока
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

### Добавить свой обработчик в бота

```python
from aiogram import types
from engine import GameBot
from commands.heal import HealCommand

class MyGameBot(GameBot):
    """Расширенный бот с пользовательскими командами."""
    
    def _register_handlers(self):
        super()._register_handlers()
        
        @self.dp.message(Command("heal"))
        async def heal_handler(message: types.Message):
            user_id = str(message.from_user.id)
            
            # Выполнить команду лечения
            result = await self.executor.execute(
                HealCommand(user_id, 50)
            )
            
            if result.success:
                await message.answer(
                    f"❤️ Вы восстановили {result.data['healed']} HP!\n"
                    f"Текущее HP: {result.data['new_hp']}"
                )
            else:
                await message.answer(f"❌ Ошибка: {result.error}")

# Использовать вместо GameBot
bot = MyGameBot(token=TELEGRAM_BOT_TOKEN, state=state, executor=executor)
```

## 📊 Расширение игры

### Добавить больше контента

1. **Новые мобы:** создайте JSON файлы в `data/mobs/`
2. **Новые предметы:** создайте JSON файлы в `data/items/`
3. **Новые механики:** создайте пользовательские команды
4. **Новые модули:** подпишитесь на события для реактивной логики

### Добавить достижения

```python
from engine import AchievementModule

# В main()
achievement_module = AchievementModule(state, event_bus)

# Достижения будут автоматически выдаваться при убийстве мобов
```

### Добавить квесты

Создайте `data/quests/first_quest.json` и `modules/quest_module.py` по аналогии с существующими модулями.

## 🐛 Отладка

### Проверить загруженные данные

```python
from engine import get_global_loader

loader = get_global_loader()
loader.load_category("mobs", "mob_schema.json")

# Посмотреть всех мобов
all_mobs = loader.get_all("mobs")
for mob_id, mob_data in all_mobs.items():
    print(f"{mob_id}: {mob_data['name']} (HP: {mob_data['hp']})")
```

### Посмотреть состояние игрока

```python
player = state.get_entity("player_123")
print(f"Gold: {player.get('gold', 0)}")
print(f"Level: {player.get('level', 1)}")
print(f"HP: {player.get('hp', 100)}")
```

### Включить подробное логирование

```python
logging.basicConfig(level=logging.DEBUG)
```

## 🆕 Новые возможности (v0.5.6+)

Движок теперь поддерживает продвинутые системы для CCG/Gacha игр:

### Bulk Loading - Быстрая загрузка коллекций
```python
# Вместо 30 отдельных запросов:
deck_ids = player["deck_card_ids"]
cards = state.get_entities_bulk(deck_ids)  # 1 SQL запрос, ~25x быстрее!
```

### Media Albums - Красивые gacha результаты
```python
from engine.adapters.telegram import ResponseBuilder

builder = ResponseBuilder()
album = builder.build_media_album(cards, media_library=get_media_library())
await message.answer_media_group(album)  # Альбом вместо 10 сообщений
```

### Gacha Service - Pity System
```python
from engine.services import GachaService, PityConfig

service = GachaService(PityConfig(soft_pity_start=70, hard_pity=90))
result = service.single_pull(player, card_pool)
```

**Подробнее:**
- [Aether Bonds Guide](../templates/card_game/AETHER_BONDS_GUIDE.md) - полный гайд по CCG играм
- [Templates Guide](TEMPLATES_GUIDE.md) - паттерны и примеры

---

## 📚 Следующие шаги

1. **Изучите примеры:** посмотрите `examples/advanced_bot.py` в репозитории движка
2. **Прочитайте документацию:** [USAGE.md](USAGE.md) и [API_REFERENCE.md](API_REFERENCE.md)
3. **Попробуйте шаблоны:** [TEMPLATES_GUIDE.md](TEMPLATES_GUIDE.md) - RPG, Idle, CCG
4. **Добавьте больше контента:** мобы, предметы, локации
5. **Создайте уникальные механики:** пользовательские команды и модули
6. **Балансировка:** настройте сложность и награды

## 🎉 Поздравляем!

Вы создали свою первую игру на Telegram Game Engine! 

Присоединяйтесь к сообществу:
- **GitHub:** https://github.com/yourusername/tg_bot_engine
- **Telegram:** @tg_bot_engine_chat
- **Примеры игр:** https://github.com/yourusername/tg_bot_engine/wiki/Showcases

