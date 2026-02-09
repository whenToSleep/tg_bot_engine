# 📚 API Reference - Telegram Game Engine

Полная документация всех классов и методов Telegram Game Engine.

## Содержание

- [Core](#core)
  - [Command](#command)
  - [CommandResult](#commandresult)
  - [GameState](#gamestate)
  - [PersistentGameState](#persistentgamestate)
  - [CommandExecutor](#commandexecutor)
  - [AsyncCommandExecutor](#asynccommandexecutor)
- [Persistence](#persistence)
  - [EntityRepository](#entityrepository)
  - [SQLiteRepository](#sqliterepository)
- [Transactions](#transactions)
  - [Transaction](#transaction)
  - [TransactionalExecutor](#transactionalexecutor)
- [Data Loading](#data-loading)
  - [DataLoader](#dataloader)
- [Events](#events)
  - [Event](#event)
  - [EventBus](#eventbus)
- [Modules](#modules)
  - [AchievementModule](#achievementmodule)
  - [ProgressionModule](#progressionmodule)
- [Commands](#commands)
  - [Economy Commands](#economy-commands)
  - [Combat Commands](#combat-commands)
  - [Spawning Commands](#spawning-commands)
- [Telegram Adapter](#telegram-adapter)
  - [GameBot](#gamebot)
  - [TelegramCommandAdapter](#telegramcommandadapter)
  - [ResponseBuilder](#responsebuilder)
- [Utilities](#utilities)
  - [Weighted Random](#weighted-random)
  - [Idle/Clicker Utilities](#idleclicker-utilities)
  - [Collection Management](#collection-management)
- [Stat Modifiers System](#stat-modifiers-system)
  - [ModifierType](#modifiertype)
  - [Modifier](#modifier)
  - [StatCalculator](#statcalculator)
- [Bonus Calculator System](#bonus-calculator-system)
  - [BonusCalculator](#bonuscalculator)
  - [Working with Entities](#работа-с-сущностями)
- [Entity Status System](#entity-status-system)
  - [EntityStatus](#entitystatus)
  - [StatusValidator](#statusvalidator)
- [Unique Entity System](#unique-entity-system)
  - [Creating Unique Entities](#создание-уникальных-сущностей)
  - [Working with Collections](#работа-с-коллекциями)
- [Gacha Service](#gacha-service-ccggacha-games)
  - [GachaService](#gachaservice)
  - [Pity System](#мульти-крутка-10x)
- [Matchmaking Service](#matchmaking-service-pvp)
  - [MatchmakingService](#matchmakingservice)
  - [Leaderboards](#leaderboard)
- [Media Library](#media-library-telegram)
  - [MediaLibrary](#medialibrary)

---

## Core

### Command

Базовый класс для всех игровых команд.

```python
from engine import Command, GameState

class Command:
    """Абстрактный базовый класс для команд."""
    
    def get_entity_dependencies(self) -> List[str]:
        """Вернуть список ID сущностей, необходимых для выполнения.
        
        Returns:
            List[str]: Список ID сущностей
        """
        pass
    
    def execute(self, state: GameState) -> Dict[str, Any]:
        """Выполнить команду.
        
        Args:
            state: Игровое состояние
            
        Returns:
            Dict[str, Any]: Результат выполнения
            
        Raises:
            ValueError: Если команда не может быть выполнена
        """
        pass
```

**Пример:**

```python
class GiveItemCommand(Command):
    def __init__(self, player_id: str, item_id: str):
        self.player_id = player_id
        self.item_id = item_id
    
    def get_entity_dependencies(self) -> List[str]:
        return [self.player_id]
    
    def execute(self, state: GameState) -> Dict[str, Any]:
        player = state.get_entity(self.player_id)
        if not player:
            raise ValueError(f"Player {self.player_id} not found")
        
        inventory = player.get("inventory", {})
        inventory[self.item_id] = inventory.get(self.item_id, 0) + 1
        player["inventory"] = inventory
        state.set_entity(self.player_id, player)
        
        return {"item_id": self.item_id, "count": inventory[self.item_id]}
```

### CommandResult

Результат выполнения команды.

```python
from engine import CommandResult

class CommandResult:
    """Результат выполнения команды."""
    
    def __init__(self, success: bool, data: Dict[str, Any], error: Optional[str] = None):
        """
        Args:
            success: Успешно ли выполнена команда
            data: Данные результата
            error: Сообщение об ошибке (если есть)
        """
        self.success = success
        self.data = data
        self.error = error
    
    @staticmethod
    def success_result(data: Dict[str, Any]) -> CommandResult:
        """Создать успешный результат."""
        return CommandResult(success=True, data=data)
    
    @staticmethod
    def error_result(error: str) -> CommandResult:
        """Создать результат с ошибкой."""
        return CommandResult(success=False, data={}, error=error)
```

### GameState

Управление игровыми сущностями в памяти.

```python
from engine import GameState

class GameState:
    """Хранилище игровых сущностей."""
    
    def set_entity(self, entity_id: str, data: Dict[str, Any]) -> None:
        """Установить или обновить сущность.
        
        Args:
            entity_id: Уникальный идентификатор
            data: Данные сущности
        """
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Получить сущность по ID.
        
        Args:
            entity_id: Уникальный идентификатор
            
        Returns:
            Optional[Dict[str, Any]]: Данные сущности или None
        """
    
    def exists(self, entity_id: str) -> bool:
        """Проверить существование сущности.
        
        Args:
            entity_id: Уникальный идентификатор
            
        Returns:
            bool: True если сущность существует
        """
    
    def delete_entity(self, entity_id: str) -> None:
        """Удалить сущность.
        
        Args:
            entity_id: Уникальный идентификатор
        """
    
    def get_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Получить все сущности определённого типа.
        
        Args:
            entity_type: Тип сущности (из поля _type)
            
        Returns:
            List[Dict[str, Any]]: Список сущностей
            
        Example:
            >>> players = state.get_entities_by_type("player")
            >>> for player in players:
            ...     print(player["name"])
        """
    
    def get_entities_by_filter(
        self, 
        filter_func: Callable[[Dict[str, Any]], bool]
    ) -> List[Dict[str, Any]]:
        """Получить сущности по кастомному фильтру.
        
        Args:
            filter_func: Функция-предикат для фильтрации
            
        Returns:
            List[Dict[str, Any]]: Отфильтрованные сущности
            
        Example:
            >>> high_level = state.get_entities_by_filter(
            ...     lambda e: e.get("level", 0) > 10
            ... )
        """
    
    def get_all_entities(self) -> Dict[str, Dict[str, Any]]:
        """Получить все сущности.
        
        Returns:
            Dict[str, Dict[str, Any]]: Словарь entity_id -> entity_data
            
        Warning:
            Возвращает ссылку на внутреннее хранилище!
        """
    
    def entity_count(self) -> int:
        """Получить общее количество сущностей.
        
        Returns:
            int: Количество сущностей
        """
    
    def clear(self) -> None:
        """Очистить все сущности."""
```

### PersistentGameState

GameState с автоматическим сохранением в БД.

```python
from engine import PersistentGameState, SQLiteRepository

class PersistentGameState(GameState):
    """Персистентное состояние с сохранением в БД."""
    
    def __init__(self, repository: EntityRepository, auto_flush: bool = True):
        """
        Args:
            repository: Репозиторий для хранения
            auto_flush: Автоматически сохранять изменения
        """
    
    def flush(self) -> None:
        """Сохранить все изменения в репозиторий."""
    
    def flush_entity(self, entity_id: str) -> None:
        """Сохранить конкретную сущность.
        
        Args:
            entity_id: ID сущности для сохранения
        """
    
    def reload(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Перезагрузить сущность из репозитория.
        
        Args:
            entity_id: ID сущности
            
        Returns:
            Optional[Dict[str, Any]]: Данные из БД
        """
    
    def get_entities_bulk(self, entity_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Загрузить множество сущностей оптимизированно (v0.5.6+).
        
        Использует bulk loading из репозитория для быстрой загрузки коллекций.
        ~25x быстрее чем последовательные get_entity() вызовы.
        
        Args:
            entity_ids: Список ID сущностей
            
        Returns:
            Dict[str, Dict]: Словарь entity_id -> entity_data
            
        Example:
            >>> # Загрузить колоду игрока (30 карт)
            >>> deck_ids = player["deck_card_ids"]
            >>> cards = state.get_entities_bulk(deck_ids)
            >>> for card_id, card in cards.items():
            ...     print(f"{card['name']}: {card['attack']}")
        """
```

**Пример:**

```python
repo = SQLiteRepository("game.db")
state = PersistentGameState(repo, auto_flush=True)

# Автоматически сохраняется в БД
state.set_entity("player_1", {"_type": "player", "gold": 100})

# Ручное сохранение (если auto_flush=False)
state.set_entity("player_2", {"_type": "player", "gold": 50})
state.flush()

# Bulk loading (v0.5.6+) - загрузка коллекций
deck_ids = player.get("deck_card_ids", [])
cards = state.get_entities_bulk(deck_ids)
# ~25x быстрее чем 30 вызовов get_entity()!

for card_id, card in cards.items():
    print(f"Карта: {card['name']}, Атака: {card['attack']}")
```

### CommandExecutor

Синхронный исполнитель команд.

```python
from engine import CommandExecutor

class CommandExecutor:
    """Синхронный исполнитель команд."""
    
    def execute(self, command: Command, state: GameState) -> CommandResult:
        """Выполнить команду.
        
        Args:
            command: Команда для выполнения
            state: Игровое состояние
            
        Returns:
            CommandResult: Результат выполнения
        """
```

### AsyncCommandExecutor

Асинхронный исполнитель с блокировками.

```python
from engine import AsyncCommandExecutor

class AsyncCommandExecutor:
    """Асинхронный исполнитель с блокировками."""
    
    def __init__(self, state: GameState, lock_timeout: float = 5.0):
        """
        Args:
            state: Игровое состояние
            lock_timeout: Таймаут ожидания блокировки (секунды)
        """
    
    async def execute(self, command: Command) -> CommandResult:
        """Выполнить команду асинхронно.
        
        Args:
            command: Команда для выполнения
            
        Returns:
            CommandResult: Результат выполнения
        """
```

**Пример:**

```python
executor = AsyncCommandExecutor(state)

# Автоматические блокировки на сущности
result = await executor.execute(GainGoldCommand("player_1", 100))

if result.success:
    print(f"New gold: {result.data['new_gold']}")
```

---

## Persistence

### EntityRepository

Абстрактный интерфейс репозитория.

```python
from engine import EntityRepository

class EntityRepository(ABC):
    """Абстрактный репозиторий сущностей."""
    
    @abstractmethod
    def save(self, entity_id: str, entity_data: dict) -> None:
        """Сохранить сущность."""
    
    @abstractmethod
    def load(self, entity_id: str) -> Optional[dict]:
        """Загрузить сущность."""
    
    @abstractmethod
    def delete(self, entity_id: str) -> None:
        """Удалить сущность."""
    
    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Проверить существование."""
    
    @abstractmethod
    def list_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Получить список по типу."""
    
    @abstractmethod
    def count(self, entity_type: Optional[str] = None) -> int:
        """Подсчитать сущности."""
    
    @abstractmethod
    def clear(self) -> None:
        """Очистить все сущности."""
```

### SQLiteRepository

SQLite реализация репозитория.

```python
from engine import SQLiteRepository

class SQLiteRepository(EntityRepository):
    """Репозиторий на базе SQLite."""
    
    def __init__(self, db_path: str = "game.db"):
        """
        Args:
            db_path: Путь к файлу БД (или ":memory:" для in-memory)
        """
```

**Основные методы:**

```python
# Загрузить одну сущность
entity = repo.load("player_1")

# Загрузить множество сущностей (BULK, v0.5.6+)
deck_ids = ["card_1", "card_2", "card_3", ...]
cards = repo.load_bulk(deck_ids)
# Возвращает: {"card_1": {...}, "card_2": {...}, ...}

# Сохранить сущность
repo.save("player_1", player_data)

# Удалить сущность
repo.delete("player_1")

# Проверить существование
if repo.exists("player_1"):
    print("Игрок существует")

# Список ID по типу
player_ids = repo.list_by_type("player")

# Подсчёт сущностей
count = repo.count()
```

**Особенности:**
- ✅ Оптимистичные блокировки (optimistic locking)
- ✅ Версионирование сущностей
- ✅ Индексы по типам
- ✅ ACID гарантии
- ✅ **Bulk loading** (v0.5.6+) - загрузка коллекций одним запросом

**load_bulk() Performance:**

| Операция | Обычный способ | Bulk loading | Улучшение |
|----------|----------------|--------------|-----------|
| 30 карт | 30 SQL queries (~500ms) | 1 SQL query (~20ms) | **25x** |
| 100 карт | 100 SQL queries (~1.5s) | 1 SQL query (~50ms) | **30x** |

---

## Transactions

### Transaction

Транзакция для атомарных операций.

```python
from engine import Transaction

class Transaction:
    """Транзакция с snapshot-based изоляцией."""
    
    def __init__(self, state: GameState):
        """
        Args:
            state: Исходное состояние
        """
        self.state = state
        self.work_state = GameState()  # Рабочее состояние
        self.is_active = True
    
    def commit(self) -> None:
        """Применить изменения к исходному состоянию."""
    
    def rollback(self) -> None:
        """Откатить транзакцию."""
```

### TransactionalExecutor

Исполнитель с поддержкой транзакций.

```python
from engine import TransactionalExecutor

executor = TransactionalExecutor(state)
tx = Transaction(state)

# Выполнить в транзакции
result1 = executor.execute(Command1(), tx.work_state)
result2 = executor.execute(Command2(), tx.work_state)

if result1.success and result2.success:
    tx.commit()
else:
    tx.rollback()
```

---

## Data Loading

### DataLoader

Загрузка игрового контента из JSON.

```python
from engine import DataLoader, get_global_loader

class DataLoader:
    """Загрузчик игровых данных."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Args:
            data_dir: Базовая директория с данными
        """
    
    def load_category(
        self,
        category: str,
        schema_name: str,
        schema_dir: str = "schemas"
    ) -> int:
        """Загрузить категорию данных.
        
        Args:
            category: Имя категории (например, "mobs")
            schema_name: Имя файла JSON схемы
            schema_dir: Директория со схемами
            
        Returns:
            int: Количество загруженных файлов
        """
    
    def get(self, category: str, data_id: str) -> Optional[Dict[str, Any]]:
        """Получить данные по ID.
        
        Args:
            category: Категория
            data_id: ID данных
            
        Returns:
            Optional[Dict[str, Any]]: Данные или None
        """
    
    def get_all(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Получить все данные категории.
        
        Args:
            category: Категория
            
        Returns:
            Dict[str, Dict[str, Any]]: Все данные
        """
    
    def is_loaded(self, category: str) -> bool:
        """Проверить загружена ли категория.
        
        Args:
            category: Категория
            
        Returns:
            bool: True если загружена
        """
    
    def get_stats(self) -> Dict[str, int]:
        """Получить статистику загруженных данных.
        
        Returns:
            Dict[str, int]: {"category": count, ...}
        """
```

**Пример:**

```python
loader = get_global_loader()
loader.set_data_directory("data")

# Загрузить мобов
loader.load_category("mobs", "mob_schema.json")

# Получить моба
goblin = loader.get("mobs", "goblin_warrior")
print(f"HP: {goblin['hp']}")

# Получить всех мобов
all_mobs = loader.get_all("mobs")
```

---

## Events

### Event

Базовый класс события.

```python
from engine import Event
from dataclasses import dataclass

@dataclass
class Event:
    """Базовый класс игрового события."""
    pass

# Встроенные события:
@dataclass
class MobKilledEvent(Event):
    mob_id: str
    killer_id: str

@dataclass
class PlayerLevelUpEvent(Event):
    player_id: str
    old_level: int
    new_level: int

@dataclass
class GoldChangedEvent(Event):
    player_id: str
    old_gold: int
    new_gold: int
    change: int

@dataclass
class AchievementUnlockedEvent(Event):
    player_id: str
    achievement_id: str

@dataclass
class MobSpawnedEvent(Event):
    mob_id: str
    template_id: str

@dataclass
class ItemSpawnedEvent(Event):
    item_id: str
    template_id: str
    owner_id: str
```

### EventBus

Шина событий для pub/sub.

```python
from engine import EventBus, get_event_bus

class EventBus:
    """Шина событий."""
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Подписаться на событие.
        
        Args:
            event_type: Тип события (имя класса)
            handler: Функция-обработчик
        """
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Отписаться от события."""
    
    def publish(self, event: Event) -> None:
        """Опубликовать событие.
        
        Args:
            event: Экземпляр события
        """
    
    def clear(self) -> None:
        """Очистить все подписки."""
```

**Пример:**

```python
event_bus = get_event_bus()

# Подписаться
def on_levelup(event):
    print(f"Player {event.player_id} reached level {event.new_level}!")

event_bus.subscribe("PlayerLevelUpEvent", on_levelup)

# Опубликовать
event_bus.publish(PlayerLevelUpEvent(
    player_id="player_1",
    old_level=5,
    new_level=6
))
```

---

## Modules

### AchievementModule

Модуль достижений.

```python
from engine import AchievementModule

module = AchievementModule(state, event_bus)

# Автоматически:
# - Подписывается на MobKilledEvent
# - Отслеживает убийства мобов
# - Выдаёт достижения
# - Публикует AchievementUnlockedEvent
```

**Встроенные достижения:**
- `goblin_slayer` - убить 10 гоблинов
- `orc_hunter` - убить 5 орков  
- `dragon_slayer` - убить 1 дракона

### ProgressionModule

Модуль прогрессии и левелинга.

```python
from engine import ProgressionModule

module = ProgressionModule(state, event_bus)

# Автоматически:
# - Подписывается на MobKilledEvent
# - Начисляет опыт игроку
# - Повышает уровни
# - Публикует PlayerLevelUpEvent
```

**Параметры:**
- Начальный уровень: 1
- Базовый опыт до 2-го уровня: 100
- Формула: `exp_to_next = base_exp * new_level`

---

## Commands

### Economy Commands

#### GainGoldCommand

```python
from engine import GainGoldCommand

cmd = GainGoldCommand(player_id="player_1", amount=100)
result = await executor.execute(cmd)

# result.data:
# {
#     "old_gold": 50,
#     "new_gold": 150,
#     "gained": 100
# }
```

#### SpendGoldCommand

```python
from engine import SpendGoldCommand

cmd = SpendGoldCommand(player_id="player_1", amount=50)
result = await executor.execute(cmd)

# Ошибка если недостаточно золота
# result.success = False
# result.error = "Insufficient gold"
```

### Combat Commands

#### AttackMobCommand

```python
from engine import AttackMobCommand

cmd = AttackMobCommand(player_id="player_1", mob_id="mob_123")
result = await executor.execute(cmd)

# result.data:
# {
#     "damage_dealt": 15,
#     "mob_hp": 35,
#     "mob_killed": False,
#     "gold_gained": 0,  # если убит
#     "exp_gained": 0    # если убит
# }
```

### Spawning Commands

#### SpawnMobCommand

```python
from engine import SpawnMobCommand

cmd = SpawnMobCommand(
    mob_template_id="goblin_warrior",
    instance_id="mob_123"
)
result = await executor.execute(cmd)

# result.data:
# {
#     "spawned_id": "mob_123",
#     "template_id": "goblin_warrior",
#     "name": "Гоблин",
#     "hp": 30,
#     "attack": 5
# }
```

#### SpawnItemCommand

```python
from engine import SpawnItemCommand

cmd = SpawnItemCommand(
    item_template_id="health_potion",
    instance_id="item_456",
    owner_id="player_1",
    quantity=1
)
result = await executor.execute(cmd)
```

---

## Telegram Adapter

### GameBot

Основной класс Telegram бота.

```python
from engine import GameBot

bot = GameBot(
    token="YOUR_BOT_TOKEN",
    state=persistent_state,
    executor=async_executor
)

await bot.start()  # Запустить polling
await bot.stop()   # Остановить бота
```

**Встроенные команды:**
- `/start` - начать игру
- `/fight` - сразиться с мобом
- `/profile` - посмотреть статистику
- `/claim_daily` - получить ежедневную награду
- `/shop` - открыть магазин

### TelegramCommandAdapter

Преобразование Telegram updates в команды.

```python
from engine import TelegramCommandAdapter

adapter = TelegramCommandAdapter(executor)

# Обработать callback
result = await adapter.handle_callback(callback_query)

# Обработать команду
result = await adapter.handle_command(message)
```

### ResponseBuilder

Форматирование результатов для Telegram.

```python
from engine import ResponseBuilder

builder = ResponseBuilder()

# Построить ответ для боя
response = builder.build_combat_result(result, mob_id="mob_123")

# response:
# {
#     "text": "⚔️ Вы нанесли 15 урона!\n❤️ HP моба: 35",
#     "reply_markup": InlineKeyboardMarkup(...)
# }

await message.answer(
    response['text'],
    reply_markup=response['reply_markup']
)
```

---

## Utilities

Вспомогательные функции для игровой механики.

### Weighted Random

```python
from engine.core import utils

# Weighted choice для лута
loot_table = [
    {"item_id": "sword", "weight": 70},
    {"item_id": "gem", "weight": 30}
]
result = utils.weighted_choice(loot_table, "weight")
print(result["item_id"])  # "sword" (70%) или "gem" (30%)

# Roll loot table
loot = [
    {"item_id": "gold", "chance": 1.0, "min_quantity": 5, "max_quantity": 10},
    {"item_id": "gem", "chance": 0.1}
]
dropped = utils.roll_loot_table(loot)
# ['gold', 'gold', 'gold', ...] и иногда 'gem'

# Gacha pull
cards = [
    {"id": "card1", "rarity": "common"},
    {"id": "card2", "rarity": "legendary"}
]
rarity_weights = {"common": 99, "legendary": 1}
pulled = utils.gacha_pull(cards, rarity_weights)
```

### Idle/Clicker Utilities

```python
from engine.core import utils
import time

# Offline progress
last_login = time.time() - 10 * 3600  # 10 часов назад
now = time.time()
result = utils.calculate_offline_progress(
    last_login, now, 
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

### Collection Management

```python
from engine.core import utils

# Merge stacks
inventory = {"potion": 95}
result = utils.merge_item_stacks(inventory, "potion", 10, max_stack=99)
# {"added": 4, "overflow": 6, "new_quantity": 99}
```

**Доступные функции:**
- `weighted_choice()` - выбор с весами
- `roll_loot_table()` - roll для лут-таблицы
- `gacha_pull()` - gacha pull с рарностями
- `calculate_offline_progress()` - офлайн прогресс
- `calculate_exponential_cost()` - экспоненциальная стоимость
- `calculate_exponential_production()` - экспоненциальное производство
- `merge_item_stacks()` - объединение стаков
- `filter_entities()` - фильтрация сущностей

---

## Stat Modifiers System

Система модификаторов для баффов, дебаффов и динамических статов (для RPG).

### ModifierType

```python
from engine.core.modifiers import ModifierType

class ModifierType(Enum):
    FLAT = "flat"          # +10 attack
    PERCENT = "percent"    # +20% attack (x1.2)
    MULTIPLY = "multiply"  # x2 attack
```

### Modifier

```python
from engine.core.modifiers import Modifier, ModifierType

# Создать бафф: +50% атаки на 3 хода
buff = Modifier("attack", ModifierType.PERCENT, 0.5, "buff_strength", duration=3)

# Добавить к сущности
entity = {"base_attack": 10, "modifiers": []}
entity["modifiers"].append(buff.to_dict())

# Применить модификатор вручную
final_value = buff.apply(10)  # 15.0
```

**Основные методы:**
- `apply(base_value)` - применить модификатор к базовому значению
- `tick()` - уменьшить длительность на 1 ход
- `to_dict()` / `from_dict()` - сериализация

### StatCalculator

```python
from engine.core.modifiers import StatCalculator, add_modifier

# Создать сущность с модификаторами
entity = {
    "base_attack": 10,
    "base_defense": 5,
    "base_hp": 100,
    "modifiers": []
}

# Добавить модификаторы
add_modifier(entity, "attack", "flat", 5, "item_sword")
add_modifier(entity, "attack", "percent", 0.2, "buff_strength", duration=3)

# Рассчитать финальные статы
stats = StatCalculator.get_all_stats(entity)
print(stats["attack"])  # 18.0 = (10 + 5) * 1.2
print(stats["defense"])  # 5.0
print(stats["hp"])  # 100.0

# Обновить длительность (конец хода)
expired = StatCalculator.update_modifier_durations(entity)
```

**Порядок применения:**
1. Суммировать все FLAT модификаторы
2. Умножить на (1 + сумма PERCENT модификаторов)
3. Умножить на произведение всех MULTIPLY модификаторов

**Вспомогательные функции:**
```python
from engine.core.modifiers import (
    add_modifier,
    remove_modifiers_by_source,
    has_modifier_from_source
)

# Добавить модификатор
add_modifier(entity, "attack", "percent", 0.3, "buff_berserk", duration=5)

# Удалить модификаторы от источника
count = remove_modifiers_by_source(entity, "buff_berserk")

# Проверить наличие
has_buff = has_modifier_from_source(entity, "buff_berserk")
```

---

## Bonus Calculator System

Система расчёта бонусов для idle/clicker игр с множителями из разных источников.

### BonusCalculator

```python
from engine.core.bonuses import BonusCalculator

calc = BonusCalculator()

# Добавить бонусы от разных источников
calc.add_bonus("production", "percent", 0.05, "achievement_novice")
calc.add_bonus("production", "percent", 0.10, "item_hammer")
calc.add_bonus("production", "flat", 5, "upgrade_factory")

# Установить лимит
calc.add_cap("production", 1000)

# Рассчитать финальное значение
base_production = 10
final = calc.calculate("production", base_production)
# (10 + 5) * (1 + 0.05 + 0.10) = 17.25
```

**Основные методы:**
- `add_bonus(category, type, value, source)` - добавить бонус
- `remove_bonus(category, source)` - удалить бонусы от источника
- `add_cap(category, cap_value)` - установить максимальный лимит
- `calculate(category, base_value, apply_cap=True)` - рассчитать финальное значение
- `to_dict()` / `from_dict()` - сериализация

### Работа с сущностями

```python
from engine.core.bonuses import (
    load_bonuses_from_entity,
    save_bonuses_to_entity,
    calculate_bonus_summary
)

# Загрузить из сущности
player = {"bonuses": {...}}
calc = load_bonuses_from_entity(player)

# Сохранить в сущность
save_bonuses_to_entity(player, calc)

# Получить сводку бонусов
summary = calculate_bonus_summary(calc, "gold")
# {
#     "flat_total": 100,
#     "percent_total": 0.3,  # 30%
#     "multiply_total": 2.0,
#     "cap": 10000,
#     "sources": ["achievement_1", "item_ring"]
# }
```

**Пример использования в idle игре:**

```python
# Создать калькулятор для игрока
calc = BonusCalculator()

# Бонусы от ачивок
calc.add_bonus("offline_hours", "flat", 2, "achievement_night_owl")
calc.add_cap("offline_hours", 8)

# Бонусы от предметов
calc.add_bonus("gold_production", "percent", 0.15, "item_golden_pickaxe")

# Бонусы от апгрейдов
calc.add_bonus("gold_production", "multiply", 2.0, "upgrade_double_gold")

# Рассчитать offline прогресс с учётом бонусов
offline_hours = calc.calculate("offline_hours", 10)  # max 8 часов
base_production = 100
production = calc.calculate("gold_production", base_production)
# 100 * 1.15 * 2.0 = 230

gold_earned = production * offline_hours * 3600
```

---

## Entity Status System

Система управления статусами сущностей для сложной игровой механики (торговля, аукционы, экипировка).

### EntityStatus

```python
from engine.core.entity_status import EntityStatus, set_status, has_status

class EntityStatus(Enum):
    ACTIVE = "active"          # Норм человек: ✅ Создать множественные уникальные сущности (карты в гача-пулле)
    LOCKED = "locked"          # Заблокирован админом
    ON_AUCTION = "on_auction"  # На аукционе, нельзя использовать
    IN_TRADE = "in_trade"      # В процессе обмена
    EQUIPPED = "equipped"      # Экипирован, нельзя торговать
    CONSUMED = "consumed"      # Использован
    RESERVED = "reserved"      # Зарезервирован
```

**Основные функции:**

```python
# Установить статус
set_status(card, EntityStatus.ON_AUCTION)

# Получить статус
status = get_status(card)  # EntityStatus.ON_AUCTION

# Проверить статус
if has_status(card, EntityStatus.ACTIVE):
    # Карта доступна

# Проверить возможность использования
if is_usable(card):
    # Карту можно использовать в бою

# Проверить возможность торговли
if is_tradable(card):
    # Карту можно продать/обменять
```

**StatusValidator для команд:**

```python
from engine.core.entity_status import StatusValidator

class UsedCardCommand(Command):
    def execute(self, state):
        card = state.get_entity(self.card_id)
        
        # Требовать определённый статус
        validator = StatusValidator()
        validator.require_usable(card, "Cannot use this card")
        
        # Команда выполнится только если карта usable
        # ...
```

---

## Unique Entity System

Система создания уникальных экземпляров сущностей (критично для CCG/Gacha игр).

### Создание уникальных сущностей

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
card_instance = create_unique_entity(
    card_template,
    "card",
    owner_id="player_123",
    custom_fields={"level": 1, "exp": 0}
)

# Результат:
# {
#     "_id": "card_a1b2c3d4",           # Уникальный ID
#     "_type": "card",
#     "proto_id": "dragon_legendary",   # Ссылка на прототип
#     "name": "Ancient Dragon",
#     "rarity": "S",
#     "base_attack": 100,
#     "owner_id": "player_123",
#     "status": "active",
#     "level": 1,
#     "exp": 0
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
player_cards = state.get_entities_by_filter(
    lambda e: e.get("_type") == "card" and e.get("owner_id") == player_id
)

grouped = group_by_prototype(player_cards)
# {
#     "dragon_legendary": [card1, card2],  # 2 копии дракона
#     "goblin_common": [card3, card4, card5]  # 3 гоблина
# }

# Подсчёт коллекции
counts = count_by_prototype(player_cards)
# {"dragon_legendary": 2, "goblin_common": 3}

# Проверка одинаковости прототипа
if is_same_prototype(card1, card2):
    # Обе карты - копии одного прототипа
    pass
```

---

## Gacha Service (CCG/Gacha Games)

Сервис для gacha-системы с Pity механикой (для игр типа "Aether Bonds").

### GachaService

```python
from engine.services import GachaService, PityConfig

# Настройка pity системы
config = PityConfig(
    soft_pity_start=70,       # Мягкая гарантия с 70-й крутки
    soft_pity_increment=0.05, # +5% за каждую крутку после 70
    hard_pity=90,             # Жёсткая гарантия на 90-й крутке
    multi_guarantee_rarity="A" # Гарантия A-ранга в 10-пулле
)

service = GachaService(config)

# Одиночная крутка
player = {"_id": "player_1", "pity_counter": 75}
card_pool = get_data_loader().get_all("card")

result = service.single_pull(player, card_pool, owner_id="player_1")

# result.card - уникальный экземпляр карты
# result.rarity - редкость ("C", "B", "A", "S", "SS")
# result.was_pity - была ли это гарантия
# result.new_pity_counter - новое значение счётчика

player["pity_counter"] = result.new_pity_counter
```

**Мульти-крутка (10x):**

```python
# 10 круток с гарантией минимум одной A-ранга
results = service.multi_pull(player, card_pool, owner_id="player_1")

for result in results:
    # Добавить карту в коллекцию игрока
    state.set_entity(result.card["_id"], result.card)

player["pity_counter"] = results[-1].new_pity_counter
```

**Информация о pity:**

```python
pity_info = service.get_pity_info(player)
# {
#     "pity_counter": 75,
#     "soft_pity_active": True,
#     "pulls_until_hard_pity": 15,
#     "current_s_rate": 1.75  # Увеличенный шанс из-за soft pity
# }
```

---

## Matchmaking Service (PvP)

Сервис для подбора оппонентов и рейтинговой системы (для асинхронного PvP).

### MatchmakingService

```python
from engine.services import MatchmakingService, RankingSystem

# Инициализация
service = MatchmakingService(max_rating_diff=200)

# Инициализировать рейтинг для нового игрока
player = {"_id": "player_1"}
service.ranking.initialize_player_rating(player)
# player теперь имеет: rating=1200, rank_tier="Silver", wins=0, losses=0

# Найти оппонента
all_players = state.get_entities_by_type("player")
opponent = service.find_opponent(player, all_players)

if opponent:
    # Провести бой (ваша логика)
    player_won = True
    
    # Обновить рейтинги
    match_result = service.update_ratings_after_match(
        winner=player if player_won else opponent,
        loser=opponent if player_won else player
    )
    
    print(f"Рейтинг изменён: {match_result.winner_rating_change:+d}")
    # "Рейтинг изменён: +18" (победа над равным)
```

**Leaderboard:**

```python
# Сгенерировать топ-100
leaderboard = service.generate_leaderboard(all_players, limit=100)

for entry in leaderboard[:10]:
    print(f"{entry['rank_position']}. {entry['_id']} - {entry['rating']}")
# 1. player_42 - 2500
# 2. player_15 - 2430
# ...

# Узнать позицию конкретного игрока
rank = service.get_player_rank(player, all_players)
print(f"Ваш ранг: {rank}")
```

**Ранговые тиры:**

```python
# Получить название тира по рейтингу
tier = service.ranking.get_rank_tier(1850)  # "Platinum"

# Тиры:
# 0-1199: Bronze
# 1200-1499: Silver
# 1500-1799: Gold
# 1800-2099: Platinum
# 2100-2499: Diamond
# 2500-2999: Master
# 3000+: Grandmaster
```

---

## Media Library (Telegram)

Кэш file_id для медиа-файлов Telegram (оптимизация трафика и скорости).

### MediaLibrary

```python
from engine.adapters.telegram import MediaLibrary, get_media_library

# Глобальный экземпляр (автоматически сохраняется в media_cache.json)
library = get_media_library()

# В хендлере бота
async def send_card_image(message: Message, card_id: str):
    local_path = f"images/cards/{card_id}.png"
    
    # Проверить кэш
    file_id = library.get_file_id(local_path)
    
    if file_id:
        # Использовать закэшированный file_id
        await message.answer_photo(file_id)
    else:
        # Загрузить файл и закэшировать
        from aiogram.types import FSInputFile
        msg = await message.answer_photo(FSInputFile(local_path))
        
        # Сохранить file_id в кэш
        library.save_file_id(local_path, msg.photo[-1].file_id)
```

**Преимущества:**
- ✅ Экономия трафика (не загружать файл повторно)
- ✅ Быстрее (file_id доставляется мгновенно)
- ✅ Автосохранение кэша в JSON

---

## Raid Service (World Bosses) ⭐ NEW v0.6.0

Система глобальных боссов для кооперативных рейдов.

### RaidService

```python
from engine.services import RaidService, get_raid_service

# Инициализация
service = get_raid_service(state)

# Создать мировой рейд
raid_id = service.create_raid(
    raid_id="ancient_dragon",
    name="Ancient Dragon Lord",
    description="A legendary dragon threatens the realm",
    max_hp=1_000_000_000,  # 1 миллиард HP!
    duration_hours=48,
    reward_pool={"gems": 10000, "gold": 1000000}
)

# Активировать рейд
service.activate_raid(raid_id)

# Игрок атакует (async)
result = await service.attack_raid(
    raid_id="ancient_dragon",
    player_id="player_123",
    damage=25000
)

if result.success:
    print(f"Урон: {result.damage_dealt}")
    print(f"HP босса: {result.current_hp}/{result.max_hp}")
    print(f"Ваш ранг: {result.rank}")
    
    if result.raid_defeated:
        print("Босс повержен!")

# Получить статус рейда
status = service.get_raid_status("ancient_dragon")
print(f"Прогресс: {status['progress_percentage']:.1f}%")
print(f"Участников: {status['participant_count']}")

# Таблица лидеров
leaderboard = service.get_leaderboard("ancient_dragon", limit=10)
for entry in leaderboard:
    print(f"{entry['rank']}. {entry['player_id']}: {entry['total_damage']:,} урона")
```

**Особенности:**
- ✅ Оптимистичные блокировки (optimistic locking)
- ✅ Автоматический retry при конфликтах
- ✅ Поддержка миллиардов HP
- ✅ Отслеживание вклада каждого игрока
- ✅ Таблицы лидеров
- ✅ Ограничение по времени

**Concurrent Performance:**
- Обрабатывает 500+ одновременных атак
- Автоматический retry (до 5 попыток)
- Версионирование для предотвращения гонок

---

## Referral System (Реферальная система) ⭐ NEW v0.6.0

Система рефералов с деревом связей.

### EntityRepository Methods

```python
from engine import SQLiteRepository

repo = SQLiteRepository("game.db")

# Создать реферальную связь
repo.add_referral(
    referrer_id="veteran_player",
    referred_id="new_player"
)

# Получить дерево рефералов
tree = repo.get_referral_tree(
    player_id="veteran_player",
    depth=2,  # 2 уровня вглубь
    include_stats=True
)

print(f"Прямых рефералов: {len(tree['direct_referrals'])}")
print(f"Всего рефералов: {tree['total_referrals']}")
print(f"Уровень 1: {tree['referral_tree']['level_1']}")
print(f"Уровень 2: {tree['referral_tree']['level_2']}")

# Статистика
if tree.get('stats'):
    print(f"Общая трата: {tree['stats']['total_spending']}")
    print(f"Активных: {tree['stats']['active_referrals']}")

# Получить реферера игрока
referrer = repo.get_referrer("new_player")
print(f"Пригласил: {referrer}")

# Получить прямых рефералов
referrals = repo.get_direct_referrals("veteran_player")
print(f"Рефералов: {len(referrals)}")
```

**Структура данных игрока:**
```python
player = {
    "_type": "player",
    "_id": "player_123",
    "referrer_id": "veteran_player",  # Кто пригласил
    "referrals": ["newbie_1", "newbie_2"],  # Кого пригласил
    # ... другие поля
}
```

**Использование для бонусов:**
```python
from engine.core.bonuses import BonusCalculator

# Получить дерево рефералов
tree = repo.get_referral_tree("player_id", depth=2, include_stats=True)

# Добавить бонусы за рефералов
calc = BonusCalculator()

# Бонус за каждого прямого реферала
direct_count = len(tree['direct_referrals'])
calc.add_bonus("gold_production", "percent", direct_count * 5, "referral_bonus")

# Бонус за активных рефералов
active_count = tree['stats']['active_referrals']
calc.add_bonus("exp_gain", "percent", active_count * 2, "active_referral_bonus")
```

---

## Версии и совместимость

**Текущая версия:** 0.6.0

**Python:** 3.9+

**Зависимости:**
- `pydantic>=2.5.0` (опционально)
- `jsonschema>=4.20.0` (для валидации данных)
- `aiogram>=3.3.0` (для Telegram адаптера)

---

## Дополнительная информация

- **[USAGE.md](USAGE.md)** - Руководство по использованию
- **[QUICKSTART_GAME.md](QUICKSTART_GAME.md)** - Создание игры за 30 минут
- **[GitHub](https://github.com/yourusername/tg_bot_engine)** - Исходный код

