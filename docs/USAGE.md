# 📘 Telegram Game Engine - Руководство по использованию

Полное руководство по установке и использованию Telegram Game Engine для создания игровых ботов.

## 📦 Установка

### Из исходников (для разработки)

```bash
# Клонировать репозиторий
git clone https://github.com/yourusername/tg_bot_engine.git
cd tg_bot_engine

# Установить в режиме разработки
pip install -e .

# Установить зависимости для разработки
pip install -r requirements-dev.txt
```

### Из PyPI (в будущем)

```bash
pip install tg-bot-engine
```

## 🚀 Быстрый старт

### Минимальный пример

```python
from engine import (
    GameState,
    AsyncCommandExecutor,
    GainGoldCommand,
    PersistentGameState,
    SQLiteRepository
)

# 1. Создать хранилище
repo = SQLiteRepository("game.db")
state = PersistentGameState(repo, auto_flush=True)

# 2. Создать исполнитель команд
executor = AsyncCommandExecutor(state)

# 3. Выполнить команду
import asyncio

async def main():
    # Создать игрока
    state.set_entity("player_123", {
        "_type": "player",
        "gold": 0,
        "level": 1
    })
    
    # Дать игроку золото
    cmd = GainGoldCommand(player_id="player_123", amount=100)
    result = await executor.execute(cmd)
    
    print(f"Success: {result.success}")
    print(f"New gold: {result.data['new_gold']}")

asyncio.run(main())
```

## 🏗️ Основные компоненты

### 1. GameState - Состояние игры

Управление игровыми сущностями (игроки, мобы, предметы).

```python
from engine import GameState

state = GameState()

# Установить сущность
state.set_entity("player_1", {
    "_type": "player",
    "name": "Alice",
    "hp": 100
})

# Получить сущность
player = state.get_entity("player_1")

# Проверить существование
if state.exists("player_1"):
    print("Игрок существует")

# Получить список по типу
players = state.get_entities_by_type("player")

# Подсчитать сущности
count = state.entity_count()

# Bulk loading (v0.5.6+) - для коллекций
deck_ids = ["card_1", "card_2", "card_3", "card_4", ...]  # 30+ карт
cards = state.get_entities_bulk(deck_ids)
# Загружает все карты ОДНИМ SQL запросом (~25x быстрее!)

for card_id, card in cards.items():
    print(f"{card['name']}: {card['attack']}")
```

### 2. PersistentGameState - Персистентное состояние

Автоматическое сохранение в базу данных.

```python
from engine import PersistentGameState, SQLiteRepository

# Создать репозиторий
repo = SQLiteRepository("game.db")

# auto_flush=True - сохранять автоматически после каждого изменения
# auto_flush=False - сохранять вручную через .flush()
state = PersistentGameState(repo, auto_flush=True)

# Работает так же как GameState, но сохраняется в БД
state.set_entity("player_1", {"_type": "player", "gold": 100})

# Ручное сохранение (если auto_flush=False)
state.flush()

# Перезагрузить из БД
state.reload("player_1")
```

### 3. Commands - Игровые команды

Все действия в игре - это команды.

```python
from engine import Command, CommandResult, GameState

class MyCustomCommand(Command):
    """Пользовательская команда."""
    
    def __init__(self, player_id: str):
        self.player_id = player_id
    
    def get_entity_dependencies(self) -> list[str]:
        """Какие сущности нужны для выполнения."""
        return [self.player_id]
    
    def execute(self, state: GameState) -> dict:
        """Логика выполнения команды."""
        player = state.get_entity(self.player_id)
        
        if not player:
            raise ValueError(f"Player {self.player_id} not found")
        
        # Изменить состояние
        player["xp"] = player.get("xp", 0) + 10
        state.set_entity(self.player_id, player)
        
        # Вернуть результат
        return {
            "new_xp": player["xp"]
        }
```

### 4. AsyncCommandExecutor - Выполнение команд

Асинхронное выполнение с блокировками и транзакциями.

```python
from engine import AsyncCommandExecutor

executor = AsyncCommandExecutor(state)

# Выполнить команду
result = await executor.execute(MyCustomCommand("player_1"))

if result.success:
    print(f"XP: {result.data['new_xp']}")
else:
    print(f"Error: {result.error}")
```

### 5. DataLoader - Загрузка игрового контента

Загрузка данных из JSON файлов с валидацией по схеме.

```python
from engine import get_global_loader

loader = get_global_loader()

# Загрузить категорию данных
loader.load_category("mobs", "mob_schema.json")

# Получить данные
goblin = loader.get("mobs", "goblin_warrior")
print(f"Goblin HP: {goblin['hp']}")

# Получить все данные категории
all_mobs = loader.get_all("mobs")

# Статистика
stats = loader.get_stats()
print(f"Loaded: {stats}")
```

### 6. EventBus - Система событий

Публикация и подписка на игровые события.

```python
from engine import get_event_bus, Event

event_bus = get_event_bus()

# Определить обработчик
def on_mob_killed(event):
    print(f"Mob {event.mob_id} killed!")

# Подписаться на событие
event_bus.subscribe("MobKilledEvent", on_mob_killed)

# Опубликовать событие
from engine import MobKilledEvent
event_bus.publish(MobKilledEvent(
    mob_id="goblin_1",
    killer_id="player_1"
))
```

### 7. Modules - Игровые модули

Реактивные модули для игровой логики.

```python
from engine import AchievementModule, get_event_bus

state = PersistentGameState(repo)
event_bus = get_event_bus()

# Инициализировать модуль достижений
achievement_module = AchievementModule(state, event_bus)

# Модуль автоматически подписывается на события
# и награждает игроков достижениями
```

## 🎮 Интеграция с Telegram

### Создание бота

```python
import asyncio
from engine import (
    PersistentGameState,
    AsyncCommandExecutor,
    SQLiteRepository,
    get_event_bus,
    get_global_loader
)
from engine import GameBot  # Требует aiogram

async def main():
    # 1. Инициализировать компоненты
    repo = SQLiteRepository("game.db")
    state = PersistentGameState(repo, auto_flush=True)
    executor = AsyncCommandExecutor(state)
    
    # 2. Загрузить данные
    loader = get_global_loader()
    loader.load_category("mobs", "mob_schema.json")
    loader.load_category("items", "item_schema.json")
    
    # 3. Создать и запустить бота
    bot = GameBot(
        token="YOUR_BOT_TOKEN",
        state=state,
        executor=executor
    )
    
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Пользовательские команды для Telegram

```python
from engine.adapters.telegram import TelegramCommandAdapter
from aiogram import types

class MyTelegramAdapter(TelegramCommandAdapter):
    """Расширенный адаптер с пользовательскими командами."""
    
    async def handle_command(self, message: types.Message):
        """Обработка текстовых команд."""
        text = message.text
        user_id = str(message.from_user.id)
        
        if text == "/my_command":
            # Создать и выполнить свою команду
            result = await self.executor.execute(
                MyCustomCommand(player_id=user_id)
            )
            return result
        
        # Делегировать стандартным командам
        return await super().handle_command(message)
```

## 📊 Продвинутое использование

### Транзакции

```python
from engine import TransactionalExecutor, Transaction

# Создать транзакционный исполнитель
executor = TransactionalExecutor(state)

# Начать транзакцию
tx = Transaction(state)

# Выполнить команды в контексте транзакции
cmd1 = GainGoldCommand("player_1", 100)
cmd2 = SpendGoldCommand("player_1", 50)

result1 = executor.execute(cmd1, tx.work_state)
result2 = executor.execute(cmd2, tx.work_state)

# Если всё успешно - закоммитить
if result1.success and result2.success:
    tx.commit()
else:
    tx.rollback()
```

### Блокировки сущностей

```python
from engine import EntityLockManager

lock_manager = EntityLockManager()

async def safe_command():
    # Попытаться захватить блокировку
    lock_id = await lock_manager.acquire_lock(
        entity_id="player_1",
        timeout=5.0
    )
    
    try:
        # Выполнить операцию
        player = state.get_entity("player_1")
        player["gold"] += 100
        state.set_entity("player_1", player)
    finally:
        # Освободить блокировку
        await lock_manager.release_lock("player_1", lock_id)
```

### Пользовательские события

```python
from engine import Event
from dataclasses import dataclass

@dataclass
class QuestCompletedEvent(Event):
    """Событие завершения квеста."""
    quest_id: str
    player_id: str
    reward: int

# Опубликовать
event_bus.publish(QuestCompletedEvent(
    quest_id="first_quest",
    player_id="player_1",
    reward=500
))

# Подписаться
def on_quest_completed(event: QuestCompletedEvent):
    print(f"Quest {event.quest_id} completed!")

event_bus.subscribe("QuestCompletedEvent", on_quest_completed)
```

## 🧪 Тестирование

### Unit-тесты команд

```python
import pytest
from engine import GameState, MyCustomCommand

def test_my_command():
    # Arrange
    state = GameState()
    state.set_entity("player_1", {
        "_type": "player",
        "xp": 0
    })
    
    # Act
    cmd = MyCustomCommand("player_1")
    result = cmd.execute(state)
    
    # Assert
    assert result["new_xp"] == 10
    player = state.get_entity("player_1")
    assert player["xp"] == 10
```

### Интеграционные тесты

```python
import pytest
from engine import (
    PersistentGameState,
    SQLiteRepository,
    AsyncCommandExecutor
)

@pytest.mark.asyncio
async def test_full_flow():
    # Setup
    repo = SQLiteRepository(":memory:")
    state = PersistentGameState(repo, auto_flush=True)
    executor = AsyncCommandExecutor(state)
    
    # Create player
    state.set_entity("player_1", {
        "_type": "player",
        "gold": 0
    })
    
    # Execute command
    result = await executor.execute(
        GainGoldCommand("player_1", 100)
    )
    
    assert result.success
    assert result.data["new_gold"] == 100
```

## 🆕 Новые возможности (v0.5.6+)

### Bulk Loading для коллекций

Оптимизированная загрузка множества сущностей (~25x быстрее):

```python
from engine import PersistentGameState, SQLiteRepository

repo = SQLiteRepository("game.db")
state = PersistentGameState(repo)

# Загрузить колоду игрока (30+ карт) одним запросом
player = state.get_entity("player_123")
deck_ids = player.get("deck_card_ids", [])

# ❌ Медленно: 30 отдельных SQL запросов
# cards = [state.get_entity(card_id) for card_id in deck_ids]

# ✅ Быстро: 1 SQL запрос
cards = state.get_entities_bulk(deck_ids)

for card_id, card in cards.items():
    print(f"{card['name']}: Attack {card['attack']}")
```

### Media Albums для Telegram

Красивое отображение gacha/lootbox результатов:

```python
from engine.adapters.telegram import ResponseBuilder, get_media_library

builder = ResponseBuilder()

# Создать альбом из карт (вместо 10 отдельных сообщений)
album = builder.build_media_album(
    cards,
    media_library=get_media_library(),
    caption_formatter=lambda c, i: f"{c['rarity']} - {c['name']}"
)

# Отправить альбом
await message.answer_media_group(album)

# + текстовая сводка
summary = builder.build_gacha_result_text(cards)
await message.answer(summary)
# 🎰 Результаты гачи (10 круток)
# ⚪ C: 7 шт.
# 🔵 B: 2 шт.
# 🟣 A: 1 шт.
```

### Gacha Service с Pity System

Полноценная gacha механика для CCG игр:

```python
from engine.services import GachaService, PityConfig

# Настроить pity систему
config = PityConfig(
    soft_pity_start=70,      # Мягкая гарантия с 70-й крутки
    hard_pity=90,            # Жёсткая гарантия на 90-й
    multi_guarantee_rarity="A"  # Гарантия A-ранга в 10-крутке
)

service = GachaService(config)

# Одиночная крутка
player = state.get_entity("player_123")
card_pool = get_data_loader().get_all("card")

result = service.single_pull(player, card_pool, owner_id="player_123")
print(f"Pulled: {result.card['name']} ({result.rarity})")
print(f"Was pity: {result.was_pity}")

# Обновить счётчик
player["pity_counter"] = result.new_pity_counter
state.set_entity("player_123", player)

# 10-крутка (гарантия A-ранга)
results = service.multi_pull(player, card_pool, owner_id="player_123")
```

### Matchmaking Service для PvP

ELO-based рейтинг и подбор оппонентов:

```python
from engine.services import MatchmakingService

service = MatchmakingService(max_rating_diff=200)

# Инициализировать рейтинг нового игрока
service.ranking.initialize_player_rating(player)
# player теперь имеет: rating=1200, rank_tier="Silver", wins=0, losses=0

# Найти оппонента
all_players = state.get_entities_by_type("player")
opponent = service.find_opponent(player, all_players)

# После боя обновить рейтинги
match_result = service.update_ratings_after_match(winner, loser)
print(f"Rating change: {match_result.winner_rating_change:+d}")
print(f"New tier: {winner['rank_tier']}")
```

### Entity Status для сложных механик

Управление статусами для торговли/аукциона:

```python
from engine import EntityStatus, set_status, is_usable, is_tradable

# Выставить карту на аукцион
card = state.get_entity("card_123")
set_status(card, EntityStatus.ON_AUCTION)

# Проверки
if is_usable(card):
    print("Можно использовать в бою")  # False - на аукционе

if is_tradable(card):
    print("Можно торговать")  # False - уже на аукционе
```

### Unique Entity для CCG

Уникальные экземпляры карт:

```python
from engine import create_unique_entity, group_by_prototype

# Создать уникальную карту из прототипа
dragon_proto = get_data_loader().get("card", "ancient_dragon")

card = create_unique_entity(
    dragon_proto,
    "card",
    owner_id="player_123",
    custom_fields={"level": 1, "exp": 0}
)

# card["_id"] = "card_a1b2c3d4"  (уникальный)
# card["proto_id"] = "ancient_dragon"  (ссылка на прототип)

# Группировка коллекции
player_cards = state.get_entities_by_filter(
    lambda e: e.get("_type") == "card" and e.get("owner_id") == "player_123"
)

grouped = group_by_prototype(player_cards)
# {"ancient_dragon": [card1, card2], "goblin": [card3, card4, card5]}
```

**Подробнее:**
- [TEMPLATES_GUIDE.md](TEMPLATES_GUIDE.md) - Паттерны и примеры
- [API_REFERENCE.md](API_REFERENCE.md) - Полная документация API
- [Aether Bonds Guide](../templates/card_game/AETHER_BONDS_GUIDE.md) - CCG игры

---

## 📚 Дополнительные ресурсы

- **[QUICKSTART_GAME.md](QUICKSTART_GAME.md)** - Создание игры с нуля за 30 минут
- **[API_REFERENCE.md](API_REFERENCE.md)** - Полная документация API
- **[../examples/](../examples/)** - Примеры ботов
- **[../README.md](../README.md)** - Обзор проекта

## 🆘 Поддержка

- **Issues:** https://github.com/yourusername/tg_bot_engine/issues
- **Discussions:** https://github.com/yourusername/tg_bot_engine/discussions
- **Telegram:** @tg_bot_engine_chat

## 📄 Лицензия

MIT License - см. [LICENSE](../LICENSE)

