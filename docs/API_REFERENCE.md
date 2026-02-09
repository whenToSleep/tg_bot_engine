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
        """
    
    def entity_count(self) -> int:
        """Получить общее количество сущностей.
        
        Returns:
            int: Количество сущностей
        """
    
    def clear(self) -> None:
        """Очистить все сущности."""
    
    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Создать снимок состояния.
        
        Returns:
            Dict[str, Dict[str, Any]]: Копия всех сущностей
        """
    
    def restore(self, snapshot: Dict[str, Dict[str, Any]]) -> None:
        """Восстановить состояние из снимка.
        
        Args:
            snapshot: Снимок состояния
        """
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

**Поддерживаемые функции:**
- Оптимистичные блокировки (optimistic locking)
- Версионирование сущностей
- Индексы по типам
- ACID гарантии

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

## Версии и совместимость

**Текущая версия:** 0.5.5

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

