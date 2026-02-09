# 📖 Telegram Game Engine — Техническая документация

**Версия:** 0.6.0  
**Дата обновления:** 2026-02-09

---

## 📚 Содержание

1. [Введение](#введение)
2. [Архитектура](#архитектура)
3. [Основные компоненты](#основные-компоненты)
4. [Системы движка](#системы-движка)
5. [Сервисы](#сервисы)
6. [Команды](#команды)
7. [События](#события)
8. [Модули](#модули)
9. [Адаптеры](#адаптеры)
10. [Хранение данных](#хранение-данных)
11. [Производительность](#производительность)
12. [Лучшие практики](#лучшие-практики)

---

## Введение

### Что такое Telegram Game Engine?

**Telegram Game Engine** — это production-ready фреймворк для создания multiplayer turn-based игр в Telegram.

### Ключевые принципы

- **Command-based architecture** — все действия как атомарные команды
- **ACID гарантии** — транзакционность и откат при ошибках
- **Data-driven** — весь контент в JSON без изменения кода
- **Event-driven** — реактивная система событий
- **Персистентность** — автоматическое сохранение в БД

### Для каких игр подходит?

✅ **Подходит:**
- Turn-based RPG
- Idle/Clicker игры
- Roguelike/Roguelite
- Gacha/Collection игры (CCG)
- Card Battle игры
- Turn-based стратегии

❌ **Не подходит:**
- Real-time игры (шутеры, гонки)
- Игры с физической симуляцией
- Графически-интенсивные игры

---

## Архитектура

### Общая схема

```
┌─────────────────────────────────────────────────────────┐
│                 CLIENT LAYER (UI)                       │
│  Telegram Bot / Web UI / Discord / CLI                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              ADAPTER LAYER (Protocol)                   │
│  • Преобразует UI события → Commands                   │
│  • Преобразует Results → UI messages                    │
│  • Единственное место с async/await                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│            COMMAND LAYER (Business Logic)               │
│  • GainGoldCommand                                      │
│  • AttackMobCommand                                     │
│  • CardFusionCommand                                    │
│  • ... (пользовательские команды)                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                   ENGINE CORE                           │
│  • CommandExecutor (sync/async)                         │
│  • GameState / PersistentGameState                      │
│  • EventBus (pub/sub)                                   │
│  • TransactionManager                                   │
│  • EntityLockManager                                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│               PERSISTENCE LAYER                         │
│  • EntityRepository (interface)                         │
│  • SQLiteRepository (implementation)                    │
│  • PostgreSQLRepository (future)                        │
└─────────────────────────────────────────────────────────┘
```

### Слои ответственности

| Слой | Ответственность | Что знает |
|------|----------------|-----------|
| **Client** | UI, отображение | Ничего про игровую логику |
| **Adapter** | Преобразование протоколов | Commands + UI |
| **Commands** | Бизнес-логика игры | GameState, Events |
| **Core** | Выполнение, изоляция | Абстракции (State, Events) |
| **Persistence** | Хранение данных | SQL, файлы |

### Потоки данных

```
User Input (Telegram)
    ↓
Adapter преобразует в Command
    ↓
Executor получает блокировки на сущности
    ↓
Command изменяет GameState
    ↓
State автоматически сохраняется в БД
    ↓
Command публикует Events
    ↓
Modules реагируют на события
    ↓
Result возвращается в Adapter
    ↓
Adapter преобразует в UI message
    ↓
User видит результат
```

---

## Основные компоненты

### 1. Command (Команда)

Базовая абстракция для всех игровых действий.

**Интерфейс:**
```python
from engine import Command, GameState
from typing import List

class Command:
    """Абстрактный базовый класс команды."""
    
    def get_entity_dependencies(self) -> List[str]:
        """Вернуть ID сущностей для блокировки."""
        pass
    
    def execute(self, state: GameState) -> dict:
        """Выполнить команду. Вернуть результат."""
        pass
```

**Пример:**
```python
class GainGoldCommand(Command):
    def __init__(self, player_id: str, amount: int):
        self.player_id = player_id
        self.amount = amount
    
    def get_entity_dependencies(self) -> List[str]:
        return [self.player_id]
    
    def execute(self, state: GameState) -> dict:
        player = state.get_entity(self.player_id)
        if not player:
            raise ValueError("Player not found")
        
        old_gold = player.get("gold", 0)
        new_gold = old_gold + self.amount
        
        player["gold"] = new_gold
        state.set_entity(self.player_id, player)
        
        return {
            "old_gold": old_gold,
            "new_gold": new_gold,
            "gained": self.amount
        }
```

**Важные особенности:**

- ✅ Атомарность — команда либо выполняется полностью, либо откатывается
- ✅ Изоляция — автоматические блокировки через `get_entity_dependencies()`
- ✅ Тестируемость — чистая функция без side effects
- ✅ Переиспользование — одна команда для Telegram/Web/CLI

### 2. GameState (Состояние игры)

In-memory хранилище игровых сущностей.

**Интерфейс:**
```python
from engine import GameState

state = GameState()

# Установить сущность
state.set_entity("player_1", {
    "_type": "player",
    "_id": "player_1",
    "name": "Alice",
    "hp": 100,
    "gold": 50
})

# Получить сущность
player = state.get_entity("player_1")

# Проверить существование
if state.exists("player_1"):
    print("Player exists")

# Получить все сущности типа
players = state.get_entities_by_type("player")

# Bulk loading (v0.5.6+)
card_ids = ["card_1", "card_2", ..., "card_30"]
cards = state.get_entities_bulk(card_ids)
# Один SQL запрос вместо 30!

# Подсчитать сущности
count = state.entity_count()

# Очистить все
state.clear()
```

**Типы сущностей:**

Все сущности имеют обязательные поля:
- `_type` — тип сущности (player, mob, item, card, etc.)
- `_id` — уникальный идентификатор

**Пример сущностей:**
```python
# Игрок
{
    "_type": "player",
    "_id": "player_123",
    "name": "Alice",
    "level": 5,
    "hp": 100,
    "max_hp": 100,
    "gold": 500,
    "exp": 1250,
    "inventory": ["item_1", "item_2"]
}

# Моб
{
    "_type": "mob",
    "_id": "mob_456",
    "template_id": "goblin",
    "hp": 30,
    "max_hp": 30
}

# Предмет
{
    "_type": "item",
    "_id": "item_789",
    "template_id": "iron_sword",
    "owner_id": "player_123"
}

# Карта (для CCG игр)
{
    "_type": "card",
    "_id": "card_001",
    "template_id": "fire_dragon",
    "level": 3,
    "exp": 150,
    "owner_id": "player_123",
    "element": "fire",
    "rarity": "S"
}
```

### 3. PersistentGameState

GameState с автоматическим сохранением в БД.

**Создание:**
```python
from engine import PersistentGameState, SQLiteRepository

# Создать репозиторий
repo = SQLiteRepository("game.db")

# auto_flush=True - сохранять после каждого изменения
state = PersistentGameState(repo, auto_flush=True)

# auto_flush=False - сохранять вручную
state = PersistentGameState(repo, auto_flush=False)
state.set_entity("player_1", player_data)
state.flush()  # Явное сохранение
```

**Особенности:**

- ✅ Автоматическое сохранение при изменениях
- ✅ Lazy loading — сущности загружаются при обращении
- ✅ Crash recovery — восстановление после сбоев
- ✅ Оптимистичные блокировки — версионирование
- ✅ Zero data loss — < 2ms на сохранение

### 4. CommandExecutor

Выполнитель команд с изоляцией.

**Синхронный:**
```python
from engine import CommandExecutor, GameState

executor = CommandExecutor()
state = GameState()

result = executor.execute(command, state)
if result.success:
    print(result.data)
else:
    print(result.error)
```

**Асинхронный:**
```python
from engine import AsyncCommandExecutor

executor = AsyncCommandExecutor(state)

# Одна команда
result = await executor.execute(command)

# Batch выполнение
results = await executor.execute_batch([cmd1, cmd2, cmd3])

# Parallel execution (без race conditions!)
results = await executor.execute_parallel([cmd1, cmd2, cmd3])
```

**Гарантии:**

- ✅ Атомарность — rollback при ошибках
- ✅ Изоляция — автоматические блокировки
- ✅ Согласованность — валидация данных
- ✅ Долговечность — сохранение в БД

### 5. CommandResult

Результат выполнения команды.

**Структура:**
```python
@dataclass
class CommandResult:
    success: bool           # Успех?
    data: Dict[str, Any]    # Результаты
    error: Optional[str]    # Ошибка (если есть)
    metadata: Dict[str, Any]  # Дополнительные данные
```

**Использование:**
```python
result = executor.execute(command, state)

if result.success:
    gold = result.data['new_gold']
    print(f"Success! Gold: {gold}")
else:
    print(f"Error: {result.error}")
    
# Метаданные
events = result.metadata.get('events', [])
for event in events:
    print(f"Event: {event}")
```

---

## Системы движка

### 1. Transaction System

Управление транзакциями с rollback.

**Использование:**
```python
from engine.core.transaction import Transaction

# Создать транзакцию
tx = Transaction(state)

try:
    # Начать
    tx.begin()
    
    # Изменить данные
    player = state.get_entity("player_1")
    player["gold"] += 100
    state.set_entity("player_1", player)
    
    # Закоммитить
    tx.commit()
except Exception as e:
    # Откатить при ошибке
    tx.rollback()
    raise
```

**TransactionalExecutor:**
```python
from engine.core.transaction import TransactionalExecutor

executor = TransactionalExecutor(state)

# Автоматический rollback при ошибке!
result = executor.execute(command)
```

### 2. Entity Locking System

Предотвращение race conditions через блокировки.

**Автоматически:**
```python
# Executor автоматически блокирует сущности
# из get_entity_dependencies()

class AttackCommand(Command):
    def get_entity_dependencies(self):
        return [self.attacker_id, self.target_id]
    
    def execute(self, state):
        # Обе сущности заблокированы!
        # Никакая другая команда не может их изменить
        ...
```

**Вручную:**
```python
from engine.core.entity_lock import EntityLockManager

lock_manager = EntityLockManager()

with lock_manager.lock_entities(["player_1", "mob_1"]):
    # Критическая секция
    # Сущности заблокированы
    ...
# Автоматическое освобождение
```

**Особенности:**

- ✅ Deadlock prevention — сортировка ID
- ✅ Автоматическое освобождение
- ✅ Вложенные блокировки
- ✅ Timeout support

### 3. Event System

Pub/Sub система для реактивной логики.

**Создание событий:**
```python
from engine.core.events import Event

@dataclass
class MobKilledEvent(Event):
    player_id: str
    mob_id: str
    mob_template_id: str
    gold_gained: int
    exp_gained: int
```

**Публикация:**
```python
from engine import get_event_bus

bus = get_event_bus()

event = MobKilledEvent(
    player_id="player_1",
    mob_id="mob_1",
    mob_template_id="goblin",
    gold_gained=10,
    exp_gained=15
)

bus.publish(event)
```

**Подписка:**
```python
def on_mob_killed(event: MobKilledEvent):
    print(f"Mob killed: {event.mob_template_id}")
    print(f"Rewards: {event.gold_gained} gold")

bus.subscribe(MobKilledEvent, on_mob_killed)
```

**Встроенные события:**

- `MobKilledEvent` — убийство моба
- `LevelUpEvent` — повышение уровня
- `AchievementUnlockedEvent` — получение достижения
- `GoldGainedEvent` — получение золота
- `ItemAcquiredEvent` — получение предмета
- `QuestCompletedEvent` — завершение квеста

### 4. Data Loading System

Загрузка игрового контента из JSON.

**Структура:**
```
data/
├── schemas/
│   ├── mob_schema.json
│   ├── item_schema.json
│   └── card_schema.json
├── mobs/
│   ├── goblin.json
│   ├── orc.json
│   └── dragon.json
├── items/
│   └── health_potion.json
└── cards/
    ├── fire_dragon.json
    └── water_spirit.json
```

**Использование:**
```python
from engine import get_global_loader

loader = get_global_loader()
loader.set_data_directory("data")

# Загрузить категорию
loader.load_category("mobs", "mob_schema.json")
loader.load_category("items", "item_schema.json")

# Получить один элемент
goblin = loader.get("mobs", "goblin")
print(goblin["name"])  # "Гоблин"
print(goblin["hp"])    # 30

# Получить все элементы
all_mobs = loader.get_all("mobs")
for mob_id, mob_data in all_mobs.items():
    print(f"{mob_id}: {mob_data['name']}")

# Статистика
stats = loader.get_stats()
print(stats)  # {'mobs': 3, 'items': 1}
```

**JSON Schema валидация:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "hp", "attack"],
  "properties": {
    "name": {"type": "string"},
    "hp": {"type": "integer", "minimum": 1},
    "attack": {"type": "integer", "minimum": 0}
  }
}
```

---

## Сервисы

### 1. Gacha Service (v0.5.6+)

Система гачи для коллекционных игр.

**Создание:**
```python
from engine.services import GachaService, PityConfig

config = PityConfig(
    soft_pity_start=70,  # Мягкая жалость с 70 крутки
    hard_pity=90,        # Гарантия на 90 крутке
    rate_increase_per_pull=0.06  # +6% за крутку
)

service = GachaService(pity_config=config)
```

**Одна крутка:**
```python
card = service.single_pull(
    player=player,
    card_pool=all_cards,
    rarity_weights={"N": 94, "R": 5, "S": 0.95, "SS": 0.05}
)

print(f"Получено: {card['name']} ({card['rarity']})")
```

**Мульти-крутка (10x):**
```python
results = service.multi_pull(
    player=player,
    card_pool=all_cards,
    count=10
)

for card in results:
    print(f"- {card['name']} ({card['rarity']})")
```

**Особенности:**

- ✅ Pity system (мягкая + жесткая жалость)
- ✅ Гарантия SR/SSR каждые N круток
- ✅ Отслеживание истории
- ✅ Weighted random с настраиваемыми весами

### 2. Matchmaking Service (v0.5.6+)

PvP матчмейкинг и лидерборды.

**Создание:**
```python
from engine.services import MatchmakingService

service = MatchmakingService()
```

**Добавить в очередь:**
```python
service.add_to_queue(
    player_id="player_1",
    rating=1500,
    deck_power=850
)
```

**Найти матч:**
```python
match = service.find_match(
    player_id="player_1",
    max_rating_diff=200
)

if match:
    print(f"Матч найден!")
    print(f"Противник: {match['opponent_id']}")
    print(f"Рейтинг: {match['opponent_rating']}")
```

**Leaderboard:**
```python
# Обновить рейтинг
service.update_rating("player_1", 1550)

# Получить топ
top_players = service.get_leaderboard(limit=10)
for rank, player in enumerate(top_players, 1):
    print(f"{rank}. {player['player_id']}: {player['rating']}")

# Ранк игрока
rank = service.get_player_rank("player_1")
```

### 3. Scheduler Service (v0.6.0+)

Планировщик задач для временных событий.

**Запуск:**
```python
from engine.services import get_scheduler

scheduler = get_scheduler()
await scheduler.start()
```

**Одноразовая задача:**
```python
task_id = scheduler.schedule_once(
    callback=expire_banner,
    delay_seconds=7200,  # Через 2 часа
    task_name="expire_flash_banner"
)
```

**Повторяющаяся задача:**
```python
scheduler.schedule_recurring(
    callback=daily_reset,
    interval_seconds=86400,  # Каждые 24 часа
    task_name="daily_reset"
)
```

**Отмена:**
```python
scheduler.cancel_task(task_id)
```

### 4. Banner Manager (v0.6.0+)

Управление временными баннерами гачи.

**Создание:**
```python
from engine.services import get_banner_manager

manager = get_banner_manager()
```

**Flash баннер (временный):**
```python
manager.create_flash_banner(
    banner_id="fire_rateup",
    name="Fire Rate-Up!",
    description="3x S-rank rate!",
    card_pool=fire_cards,
    duration_seconds=7200,
    custom_weights={"S": 4.5, "SS": 1.5}
)
```

**Получить активный:**
```python
active = manager.get_active_banner()
if active:
    print(f"Активен: {active['name']}")
    print(f"Осталось: {active['time_remaining']}s")
```

**Leaderboard:**
```python
leaderboard = manager.get_leaderboard("fire_rateup")
for entry in leaderboard:
    print(f"{entry['rank']}. {entry['player_id']}: {entry['pulls']}")
```

### 5. Raid Service (v0.6.0+)

Глобальные рейд-боссы с миллиардами HP.

**Создание рейда:**
```python
from engine.services import get_raid_service

service = get_raid_service(state)

raid_id = service.create_raid(
    raid_id="ancient_dragon",
    name="Ancient Dragon Lord",
    description="Legendary dragon",
    max_hp=1_000_000_000,  # 1 миллиард!
    duration_hours=48
)

service.activate_raid(raid_id)
```

**Атака:**
```python
result = await service.attack_raid(
    raid_id="ancient_dragon",
    player_id="player_123",
    damage=25000
)

if result.success:
    print(f"Урон: {result.damage_dealt:,}")
    print(f"HP босса: {result.current_hp:,}/{result.max_hp:,}")
    print(f"Ваш ранг: {result.rank}")
```

**Leaderboard:**
```python
leaderboard = service.get_leaderboard("ancient_dragon", limit=10)
for entry in leaderboard:
    print(f"{entry['rank']}. {entry['player_id']}: {entry['total_damage']:,}")
```

**Особенности:**

- ✅ Optimistic locking (версионирование)
- ✅ Автоматический retry (до 5 попыток)
- ✅ Concurrent attacks (500+ одновременно)
- ✅ Поддержка миллиардов HP (int64)

---

## Команды

### Economy Commands

**GainGoldCommand:**
```python
from engine.commands.economy import GainGoldCommand

cmd = GainGoldCommand(player_id="player_1", amount=100)
result = executor.execute(cmd, state)
```

**SpendGoldCommand:**
```python
from engine.commands.economy import SpendGoldCommand

cmd = SpendGoldCommand(player_id="player_1", amount=50)
result = executor.execute(cmd, state)
# Автоматически проверяет достаточность средств
```

### Combat Commands

**AttackMobCommand:**
```python
from engine.commands.combat import AttackMobCommand

cmd = AttackMobCommand(
    attacker_id="player_1",
    target_id="mob_1"
)
result = executor.execute(cmd, state)

if result.data['mob_killed']:
    print(f"Моб убит! +{result.data['gold_gained']} золота")
```

### Spawning Commands

**SpawnMobCommand:**
```python
from engine.commands.spawning import SpawnMobCommand

cmd = SpawnMobCommand(
    mob_id="mob_123",
    template_id="goblin",
    data_loader=loader
)
result = executor.execute(cmd, state)
```

**SpawnItemCommand:**
```python
from engine.commands.spawning import SpawnItemCommand

cmd = SpawnItemCommand(
    item_id="item_456",
    template_id="health_potion",
    owner_id="player_1",
    data_loader=loader
)
result = executor.execute(cmd, state)
```

### Gacha Commands (v0.6.0+)

**GachaPullCommand:**
```python
from engine.commands.gacha_commands import GachaPullCommand

cmd = GachaPullCommand(
    player_id="player_1",
    banner_id="fire_rateup",
    count=10,  # 10x pull
    cost_per_pull=300
)
result = executor.execute(cmd, state)

cards = result.data['cards']
for card in cards:
    print(f"Получено: {card['name']} ({card['rarity']})")
```

### Fusion Commands (v0.6.0+)

**CardFusionCommand:**
```python
from engine.commands.fusion_commands import CardFusionCommand

cmd = CardFusionCommand(
    player_id="player_1",
    source_card_ids=["card_1", "card_2"],
    fusion_recipe_id="fire_fusion_lv2"
)
result = executor.execute(cmd, state, data_loader=loader)

if result.success:
    fused_card = result.metadata['fused_card']
    print(f"Создана карта: {fused_card['name']}")
```

---

## События

### Встроенные события

**MobKilledEvent:**
```python
@dataclass
class MobKilledEvent(Event):
    player_id: str
    mob_id: str
    mob_template_id: str
    gold_gained: int
    exp_gained: int
```

**LevelUpEvent:**
```python
@dataclass
class LevelUpEvent(Event):
    player_id: str
    old_level: int
    new_level: int
    stat_increases: Dict[str, int]
```

**AchievementUnlockedEvent:**
```python
@dataclass
class AchievementUnlockedEvent(Event):
    player_id: str
    achievement_id: str
    reward: Dict[str, Any]
```

### Подписка на события

```python
from engine import get_event_bus

bus = get_event_bus()

def on_level_up(event: LevelUpEvent):
    print(f"Player {event.player_id} reached level {event.new_level}!")
    
    # Выдать награду
    if event.new_level % 5 == 0:
        # Каждые 5 уровней
        cmd = GainGoldCommand(event.player_id, 500)
        executor.execute(cmd, state)

bus.subscribe(LevelUpEvent, on_level_up)
```

---

## Модули

### AchievementModule

Автоматическое отслеживание достижений.

**Настройка:**
```python
from engine.modules import AchievementModule

module = AchievementModule(state, event_bus)

# Достижения автоматически проверяются
# при событиях MobKilledEvent
```

**Встроенные достижения:**

- `first_kill` — первое убийство
- `monster_slayer` — 10 убийств
- `veteran_hunter` — 50 убийств
- `boss_killer` — убийство босса

### ProgressionModule

Система опыта и уровней.

**Настройка:**
```python
from engine.modules import ProgressionModule

module = ProgressionModule(state, event_bus)

# Автоматически повышает уровень
# при достаточном опыте
```

**Настройка опыта:**
```python
module = ProgressionModule(
    state=state,
    event_bus=event_bus,
    base_exp=100,
    exp_multiplier=1.5
)
# Уровень 2: 100 exp
# Уровень 3: 150 exp
# Уровень 4: 225 exp
```

---

## Адаптеры

### Telegram Adapter

Интеграция с Telegram через aiogram 3.x.

**GameBot:**
```python
from engine.adapters.telegram import GameBot

bot = GameBot(
    token="YOUR_BOT_TOKEN",
    state=state,
    executor=executor
)

await bot.start()
```

**Расширение:**
```python
from aiogram import types
from aiogram.filters import Command

class MyGameBot(GameBot):
    def _register_handlers(self):
        super()._register_handlers()
        
        @self.dp.message(Command("heal"))
        async def heal_handler(message: types.Message):
            # Пользовательская логика
            ...
```

**ResponseBuilder:**
```python
from engine.adapters.telegram import ResponseBuilder

builder = ResponseBuilder()

# Текстовый ответ
text = builder.build_profile(player)

# Медиа альбом
album = builder.build_media_album(cards, media_library)

# Кнопки
keyboard = builder.build_button_grid([
    ["⚔️ Атаковать", "🛡️ Защита"],
    ["💊 Использовать зелье"]
])
```

---

## Хранение данных

### SQLiteRepository

**Создание:**
```python
from engine import SQLiteRepository

repo = SQLiteRepository("game.db")
```

**Операции:**
```python
# Сохранить
repo.save_entity("player_1", player_data)

# Загрузить
player = repo.load_entity("player_1")

# Загрузить несколько (bulk)
card_ids = ["card_1", "card_2", ..., "card_30"]
cards = repo.load_entities_bulk(card_ids)
# ~25x быстрее!

# Загрузить по типу
all_players = repo.load_all_entities_of_type("player")

# Удалить
repo.delete_entity("mob_123")

# Существует?
if repo.entity_exists("player_1"):
    ...
```

**Версионирование:**
```python
# Optimistic locking
entity["_version"] = 1

# При сохранении:
# UPDATE entities SET data=?, version=version+1
# WHERE id=? AND version=?

# Если version изменилась - ConflictError
```

### Referral System (v0.6.0+)

**Создание связи:**
```python
repo.add_referral(
    referrer_id="veteran_player",
    referred_id="new_player"
)
```

**Получить дерево:**
```python
tree = repo.get_referral_tree(
    player_id="veteran_player",
    depth=2,
    include_stats=True
)

print(f"Прямых рефералов: {len(tree['direct_referrals'])}")
print(f"Всего: {tree['total_referrals']}")
print(f"Активных: {tree['stats']['active_referrals']}")
```

---

## Производительность

### Метрики

| Операция | Время | Throughput |
|----------|-------|------------|
| Выполнение команды | 0.007ms | 142,857 ops/s |
| Сохранение в БД | ~2ms | 500 saves/s |
| 1000 команд | 7.81ms | - |
| Bulk loading (30 карт) | ~2ms | ~25x быстрее |
| Concurrent attacks (500) | <100ms | - |

### Оптимизации

**Bulk Loading:**
```python
# Медленно (30 запросов):
cards = []
for card_id in deck_ids:
    card = state.get_entity(card_id)
    cards.append(card)

# Быстро (1 запрос):
cards = state.get_entities_bulk(deck_ids)
```

**Auto-flush:**
```python
# Production - auto_flush=True
state = PersistentGameState(repo, auto_flush=True)

# Testing - auto_flush=False
state = PersistentGameState(repo, auto_flush=False)
# Сохранять batch
state.flush()
```

**Entity Locking:**
```python
# Автоматическая сортировка ID для deadlock prevention
def get_entity_dependencies(self):
    return [self.player_id, self.mob_id]
# Движок автоматически сортирует: ["mob_id", "player_id"]
```

---

## Продвинутые системы

### Stat Modifiers System

Система модификаторов для баффов, дебаффов и динамических статов (RPG механики).

**ModifierType:**
```python
from engine.core.modifiers import ModifierType

class ModifierType(Enum):
    FLAT = "flat"          # +10 attack
    PERCENT = "percent"    # +20% attack (x1.2)
    MULTIPLY = "multiply"  # x2 attack
```

**Создание модификатора:**
```python
from engine.core.modifiers import Modifier, ModifierType

# Бафф: +50% атаки на 3 хода
buff = Modifier(
    stat="attack",
    modifier_type=ModifierType.PERCENT,
    value=0.5,
    source="buff_strength",
    duration=3
)

# Применить вручную
final_value = buff.apply(10)  # 15.0
```

**StatCalculator:**
```python
from engine.core.modifiers import StatCalculator, add_modifier

# Создать сущность
entity = {
    "base_attack": 10,
    "base_defense": 5,
    "modifiers": []
}

# Добавить модификаторы
add_modifier(entity, "attack", "flat", 5, "item_sword")
add_modifier(entity, "attack", "percent", 0.2, "buff_strength", duration=3)

# Рассчитать финальные статы
stats = StatCalculator.get_all_stats(entity)
print(stats["attack"])  # 18.0 = (10 + 5) * 1.2
```

**Порядок применения:**
1. Базовое значение + сумма FLAT модификаторов
2. Умножить на (1 + сумма PERCENT модификаторов)
3. Умножить на произведение MULTIPLY модификаторов

### Bonus Calculator System

Система бонусов для idle/clicker игр с множителями.

**Использование:**
```python
from engine.core.bonuses import BonusCalculator

calc = BonusCalculator()

# Добавить бонусы от разных источников
calc.add_bonus("production", "percent", 0.05, "achievement_novice")
calc.add_bonus("production", "percent", 0.10, "item_hammer")
calc.add_bonus("production", "flat", 5, "upgrade_factory")

# Установить лимит
calc.add_cap("production", 1000)

# Рассчитать
base_production = 10
final = calc.calculate("production", base_production)
# (10 + 5) * (1 + 0.05 + 0.10) = 17.25
```

**Работа с сущностями:**
```python
from engine.core.bonuses import (
    load_bonuses_from_entity,
    save_bonuses_to_entity,
    calculate_bonus_summary
)

# Загрузить из игрока
calc = load_bonuses_from_entity(player)

# Сохранить обратно
save_bonuses_to_entity(player, calc)

# Сводка бонусов
summary = calculate_bonus_summary(calc, "gold")
```

### Entity Status System

Управление статусами сущностей (торговля, экипировка, аукционы).

**Доступные статусы:**
```python
from engine.core.entity_status import EntityStatus

class EntityStatus(Enum):
    ACTIVE = "active"          # Доступна для использования
    LOCKED = "locked"          # Заблокирована
    ON_AUCTION = "on_auction"  # На аукционе
    IN_TRADE = "in_trade"      # В обмене
    EQUIPPED = "equipped"      # Экипирована
    CONSUMED = "consumed"      # Использована
    RESERVED = "reserved"      # Зарезервирована
```

**Работа со статусами:**
```python
from engine.core.entity_status import (
    set_status,
    get_status,
    has_status,
    is_usable,
    is_tradable
)

# Установить статус
set_status(card, EntityStatus.ON_AUCTION)

# Проверки
if is_usable(card):
    # Можно использовать в бою
    ...

if is_tradable(card):
    # Можно продать/обменять
    ...
```

**Валидация в командах:**
```python
from engine.core.entity_status import StatusValidator

class UseCardCommand(Command):
    def execute(self, state):
        card = state.get_entity(self.card_id)
        
        validator = StatusValidator()
        validator.require_usable(card, "Cannot use this card")
        
        # Выполнится только если карта usable
        ...
```

### Unique Entity System

Создание уникальных экземпляров сущностей (критично для CCG/Gacha).

**Создание уникальных экземпляров:**
```python
from engine.core.unique_entity import create_unique_entity

# Прототип карты
card_template = {
    "proto_id": "dragon_legendary",
    "name": "Ancient Dragon",
    "rarity": "S",
    "base_attack": 100
}

# Создать уникальный экземпляр
card = create_unique_entity(
    card_template,
    entity_type="card",
    owner_id="player_123",
    custom_fields={"level": 1, "exp": 0}
)

# Результат:
# {
#     "_id": "card_a1b2c3d4",  # Уникальный ID
#     "_type": "card",
#     "proto_id": "dragon_legendary",
#     "owner_id": "player_123",
#     "status": "active",
#     "level": 1,
#     "exp": 0,
#     ...
# }
```

**Работа с коллекциями:**
```python
from engine.core.unique_entity import (
    group_by_prototype,
    count_by_prototype,
    is_same_prototype
)

# Группировка по прототипам
grouped = group_by_prototype(player_cards)
# {"dragon_legendary": [card1, card2], "goblin_common": [card3, card4, card5]}

# Подсчёт
counts = count_by_prototype(player_cards)
# {"dragon_legendary": 2, "goblin_common": 3}

# Проверка
if is_same_prototype(card1, card2):
    # Обе карты - копии одного прототипа
    ...
```

### Utilities

Вспомогательные функции для игровой механики.

**Weighted Random:**
```python
from engine.core import utils

# Weighted choice для лута
loot_table = [
    {"item_id": "sword", "weight": 70},
    {"item_id": "gem", "weight": 30}
]
result = utils.weighted_choice(loot_table, "weight")

# Roll loot table
loot = [
    {"item_id": "gold", "chance": 1.0, "min_quantity": 5, "max_quantity": 10},
    {"item_id": "gem", "chance": 0.1}
]
dropped = utils.roll_loot_table(loot)

# Gacha pull
cards = [{"id": "card1", "rarity": "common"}, ...]
rarity_weights = {"common": 99, "legendary": 1}
pulled = utils.gacha_pull(cards, rarity_weights)
```

**Idle/Clicker Utilities:**
```python
import time

# Offline progress
last_login = time.time() - 10 * 3600  # 10 часов назад
result = utils.calculate_offline_progress(
    last_login,
    time.time(),
    production_rate_per_second=10.0,
    max_offline_hours=8
)
# {"offline_seconds": 28800, "earned": 288000, "was_capped": True}

# Exponential cost
cost = utils.calculate_exponential_cost(100, level=10, multiplier=1.15)
# 404 (стоимость 11-го уровня)

# Exponential production
production = utils.calculate_exponential_production(1.0, level=10, multiplier=1.07)
# 1.97 (производство на 10 уровне)
```

**Collection Management:**
```python
# Merge stacks
inventory = {"potion": 95}
result = utils.merge_item_stacks(inventory, "potion", 10, max_stack=99)
# {"added": 4, "overflow": 6, "new_quantity": 99}

# Filter entities
players = utils.filter_entities(
    all_entities,
    lambda e: e.get("level", 0) > 10
)
```

### Media Library

Кэширование file_id для Telegram медиа (оптимизация).

**Использование:**
```python
from engine.adapters.telegram import get_media_library

library = get_media_library()

# В хендлере
async def send_card_image(message, card_id):
    local_path = f"images/cards/{card_id}.png"
    
    # Проверить кэш
    file_id = library.get_file_id(local_path)
    
    if file_id:
        # Использовать кэш
        await message.answer_photo(file_id)
    else:
        # Загрузить и закэшировать
        from aiogram.types import FSInputFile
        msg = await message.answer_photo(FSInputFile(local_path))
        library.save_file_id(local_path, msg.photo[-1].file_id)
```

**Преимущества:**
- ✅ Экономия трафика (не загружать повторно)
- ✅ Быстрее (мгновенная доставка)
- ✅ Автосохранение кэша в JSON

---

## Лучшие практики

### 1. Всегда используйте команды

❌ **Плохо:**
```python
player = state.get_entity("player_1")
player["gold"] += 100
state.set_entity("player_1", player)
```

✅ **Хорошо:**
```python
cmd = GainGoldCommand("player_1", 100)
result = executor.execute(cmd, state)
```

### 2. Объявляйте зависимости

❌ **Плохо:**
```python
class MyCommand(Command):
    def get_entity_dependencies(self):
        return []  # Забыли!
```

✅ **Хорошо:**
```python
class MyCommand(Command):
    def get_entity_dependencies(self):
        return [self.player_id, self.target_id]
```

### 3. Используйте события

❌ **Плохо:**
```python
# Вся логика в команде
class AttackCommand(Command):
    def execute(self, state):
        # Атака
        ...
        # Проверка достижений
        ...
        # Проверка квестов
        ...
        # Проверка уровня
        ...
```

✅ **Хорошо:**
```python
class AttackCommand(Command):
    def execute(self, state):
        # Только атака
        ...
        # Опубликовать событие
        bus.publish(MobKilledEvent(...))
        # Модули среагируют сами!
```

### 4. Валидируйте данные

❌ **Плохо:**
```python
def execute(self, state):
    player["gold"] -= 100  # Может уйти в минус!
```

✅ **Хорошо:**
```python
def execute(self, state):
    if player.get("gold", 0) < 100:
        raise ValueError("Insufficient gold")
    player["gold"] -= 100
```

### 5. Используйте DataLoader

❌ **Плохо:**
```python
# Хардкод в коде
goblin_data = {
    "name": "Гоблин",
    "hp": 30,
    "attack": 5
}
```

✅ **Хорошо:**
```python
# JSON файл
goblin = loader.get("mobs", "goblin")
```

---

## Заключение

Telegram Game Engine предоставляет полный набор инструментов для создания production-ready игровых ботов.

**Ключевые преимущества:**

- ✅ Надежность — ACID гарантии, нет race conditions
- ✅ Масштабируемость — тысячи игроков одновременно
- ✅ Гибкость — data-driven, event-driven
- ✅ Производительность — < 10ms на операцию
- ✅ Документация — 100% coverage

**Следующие шаги:**

1. Прочитайте [QUICKSTART.md](QUICKSTART.md)
2. Изучите [API_REFERENCE.md](API_REFERENCE.md)
3. Попробуйте готовые шаблоны в папке `templates/`
4. Создайте свою игру!

---

**Версия:** 0.6.0  
**Дата:** 2026-02-09  
**Статус:** ✅ Production Ready
