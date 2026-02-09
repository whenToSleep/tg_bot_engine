# 🎮 Игровой движок для Telegram-ботов — Итерационная разработка

## 📋 Содержание

1. [Введение](#введение)
2. [Обзор архитектуры](#обзор-архитектуры)
3. [Итерации разработки](#итерации-разработки)
4. [Стратегия тестирования](#стратегия-тестирования)
5. [Критерии успеха](#критерии-успеха)
6. [Управление рисками](#управление-рисками)

---

## Введение

Этот документ описывает **пошаговую стратегию разработки** production-ready игрового движка для Telegram-ботов. Каждая итерация:

- ✅ **Тестируема** — имеет чёткие критерии приёмки
- ✅ **Завершена** — производит рабочий артефакт
- ✅ **Измерима** — имеет количественные метрики успеха
- ✅ **Обратима** — может быть откачена при провале валидации

### Основные принципы

1. **Построй → Измерь → Научись** (Build-Measure-Learn)
2. **Вертикальные срезы** вместо горизонтальных слоёв
3. **Рабочий софт** на каждой итерации
4. **Fail fast** — валидируй предположения рано

---

## Обзор архитектуры

### Что мы строим

```
┌─────────────────────────────────────────────┐
│        TELEGRAM BOT (UI слой)               │
├─────────────────────────────────────────────┤
│        ADAPTER (Протокольный слой)          │
├─────────────────────────────────────────────┤
│        GAME ENGINE CORE (Ядро)              │
│  • Command Executor                         │
│  • State Manager                            │
│  • Event System                             │
│  • Transaction Manager                      │
├─────────────────────────────────────────────┤
│        GAME MODULES (Модули)                │
│  • Economy  • Combat  • Progression         │
├─────────────────────────────────────────────┤
│        DATA LAYER (JSON/YAML)               │
└─────────────────────────────────────────────┘
```

### Ключевые компоненты

**Command** — атомарная операция над состоянием
**Entity** — игровая сущность (Player, Mob, Item)
**State** — снимок данных сущности
**Module** — набор связанных механик
**Adapter** — мост между платформой и движком

---

## Итерации разработки

---

# 🔄 Iteration 0: Proof of Concept (PoC)

**Длительность:** 1-2 недели  
**Цель:** Доказать жизнеспособность Command-based архитектуры

## Что делаем

### 1. Минимальное ядро

```python
# core/command.py
class Command:
    """Базовый класс команды"""
    def execute(self, state: GameState) -> CommandResult:
        raise NotImplementedError

# core/state.py
class GameState:
    """In-memory хранилище состояния"""
    def __init__(self):
        self._entities = {}
    
    def get_entity(self, entity_id: str) -> dict:
        return self._entities.get(entity_id)
    
    def set_entity(self, entity_id: str, data: dict):
        self._entities[entity_id] = data

# core/executor.py
class CommandExecutor:
    """Выполнитель команд"""
    def execute(self, command: Command, state: GameState) -> CommandResult:
        try:
            result = command.execute(state)
            return CommandResult(success=True, data=result)
        except Exception as e:
            return CommandResult(success=False, error=str(e))
```

### 2. Три базовые команды

```python
# commands/economy.py
class GainGoldCommand(Command):
    def __init__(self, player_id: str, amount: int):
        self.player_id = player_id
        self.amount = amount
    
    def execute(self, state: GameState):
        player = state.get_entity(self.player_id)
        player['gold'] += self.amount
        state.set_entity(self.player_id, player)
        return {"new_gold": player['gold']}

class SpendGoldCommand(Command):
    def __init__(self, player_id: str, amount: int):
        self.player_id = player_id
        self.amount = amount
    
    def execute(self, state: GameState):
        player = state.get_entity(self.player_id)
        if player['gold'] < self.amount:
            raise ValueError("Not enough gold")
        player['gold'] -= self.amount
        state.set_entity(self.player_id, player)
        return {"new_gold": player['gold']}

# commands/combat.py
class AttackMobCommand(Command):
    def __init__(self, player_id: str, mob_id: str):
        self.player_id = player_id
        self.mob_id = mob_id
    
    def execute(self, state: GameState):
        player = state.get_entity(self.player_id)
        mob = state.get_entity(self.mob_id)
        
        damage = player['attack']
        mob['hp'] -= damage
        
        if mob['hp'] <= 0:
            player['gold'] += mob['gold_reward']
        
        state.set_entity(self.player_id, player)
        state.set_entity(self.mob_id, mob)
        
        return {
            "damage_dealt": damage,
            "mob_hp": mob['hp'],
            "mob_killed": mob['hp'] <= 0
        }
```

### 3. Юнит-тесты

```python
# tests/test_commands.py
import pytest
from core.state import GameState
from commands.economy import GainGoldCommand, SpendGoldCommand
from commands.combat import AttackMobCommand

def test_gain_gold():
    state = GameState()
    state.set_entity("player1", {"gold": 100})
    
    cmd = GainGoldCommand("player1", 50)
    result = cmd.execute(state)
    
    assert result["new_gold"] == 150
    assert state.get_entity("player1")["gold"] == 150

def test_spend_gold_success():
    state = GameState()
    state.set_entity("player1", {"gold": 100})
    
    cmd = SpendGoldCommand("player1", 30)
    result = cmd.execute(state)
    
    assert result["new_gold"] == 70

def test_spend_gold_insufficient():
    state = GameState()
    state.set_entity("player1", {"gold": 10})
    
    cmd = SpendGoldCommand("player1", 30)
    
    with pytest.raises(ValueError, match="Not enough gold"):
        cmd.execute(state)

def test_attack_mob():
    state = GameState()
    state.set_entity("player1", {"attack": 10, "gold": 0})
    state.set_entity("mob1", {"hp": 25, "gold_reward": 50})
    
    # Первая атака
    cmd = AttackMobCommand("player1", "mob1")
    result = cmd.execute(state)
    
    assert result["damage_dealt"] == 10
    assert result["mob_hp"] == 15
    assert result["mob_killed"] == False
    
    # Вторая атака
    cmd = AttackMobCommand("player1", "mob1")
    result = cmd.execute(state)
    
    assert result["mob_hp"] == 5
    
    # Третья атака - убиваем
    cmd = AttackMobCommand("player1", "mob1")
    result = cmd.execute(state)
    
    assert result["mob_killed"] == True
    assert state.get_entity("player1")["gold"] == 50
```

## Критерии приёмки

- [ ] Все 3 команды реализованы
- [ ] Все юнит-тесты проходят (100% покрытие)
- [ ] Время выполнения 1000 команд < 100ms
- [ ] Код читаем и понятен новому разработчику

## Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| Тест-покрытие | 100% |
| Время выполнения команды | < 0.1ms |
| Количество багов | 0 |
| Читаемость кода (Code Climate) | A |

## Точки валидации

✅ **GO** если:
- Все тесты зелёные
- Команды выполняются детерминировано
- Архитектура понятна команде

❌ **NO-GO** если:
- Команды выполняются недетерминировано
- Производительность хуже целевой в 2+ раза
- Архитектура вызывает вопросы

---

# 🔄 Iteration 1: Транзакционность + Изоляция

**Длительность:** 2 недели  
**Цель:** Добавить ACID-гарантии и защиту от race conditions

## Что делаем

### 1. Transaction Manager

```python
# core/transaction.py
from copy import deepcopy
from typing import Optional

class Transaction:
    """Транзакция изменения состояния"""
    def __init__(self, state: GameState):
        self._original_state = state
        self._snapshot = deepcopy(state._entities)
        self._committed = False
    
    def get_state(self) -> GameState:
        """Получить изолированное состояние для работы"""
        temp_state = GameState()
        temp_state._entities = self._snapshot
        return temp_state
    
    def commit(self):
        """Применить изменения"""
        if self._committed:
            raise RuntimeError("Transaction already committed")
        self._original_state._entities = self._snapshot
        self._committed = True
    
    def rollback(self):
        """Откатить изменения"""
        self._snapshot = None
        self._committed = True

class TransactionalExecutor:
    """Исполнитель с транзакционностью"""
    def __init__(self, state: GameState):
        self.state = state
    
    def execute(self, command: Command) -> CommandResult:
        transaction = Transaction(self.state)
        
        try:
            work_state = transaction.get_state()
            result = command.execute(work_state)
            transaction.commit()
            return CommandResult(success=True, data=result)
        except Exception as e:
            transaction.rollback()
            return CommandResult(success=False, error=str(e))
```

### 2. Entity Locking

```python
# core/locks.py
import asyncio
from typing import Set, List
from contextlib import asynccontextmanager

class EntityLockManager:
    """Менеджер блокировок сущностей"""
    def __init__(self):
        self._locks = {}
    
    async def acquire(self, entity_ids: List[str], timeout: float = 5.0):
        """Захватить блокировки на сущности (в отсортированном порядке!)"""
        sorted_ids = sorted(entity_ids)  # Предотвращаем deadlock
        
        acquired = []
        try:
            for entity_id in sorted_ids:
                if entity_id not in self._locks:
                    self._locks[entity_id] = asyncio.Lock()
                
                lock = self._locks[entity_id]
                await asyncio.wait_for(lock.acquire(), timeout)
                acquired.append(entity_id)
            
            return acquired
        except asyncio.TimeoutError:
            # Откатываем частично захваченные блокировки
            for entity_id in acquired:
                self._locks[entity_id].release()
            raise TimeoutError(f"Failed to acquire locks: {entity_ids}")
    
    def release(self, entity_ids: List[str]):
        """Освободить блокировки"""
        for entity_id in entity_ids:
            if entity_id in self._locks:
                self._locks[entity_id].release()
    
    @asynccontextmanager
    async def lock_entities(self, entity_ids: List[str]):
        """Контекстный менеджер для блокировок"""
        acquired = await self.acquire(entity_ids)
        try:
            yield
        finally:
            self.release(acquired)
```

### 3. Async Command Executor

```python
# core/async_executor.py
class AsyncCommandExecutor:
    """Асинхронный исполнитель команд с блокировками"""
    def __init__(self, state: GameState):
        self.state = state
        self.lock_manager = EntityLockManager()
    
    async def execute(self, command: Command) -> CommandResult:
        # Команда декларирует какие сущности она затрагивает
        entity_ids = command.get_entity_dependencies()
        
        async with self.lock_manager.lock_entities(entity_ids):
            # Внутри блокировки - синхронное выполнение
            transaction = Transaction(self.state)
            
            try:
                work_state = transaction.get_state()
                result = command.execute(work_state)  # Sync!
                transaction.commit()
                return CommandResult(success=True, data=result)
            except Exception as e:
                transaction.rollback()
                return CommandResult(success=False, error=str(e))
```

### 4. Обновлённые команды

```python
# commands/base.py
from typing import List

class Command:
    """Базовый класс команды с зависимостями"""
    def get_entity_dependencies(self) -> List[str]:
        """Список сущностей, которые команда читает/пишет"""
        raise NotImplementedError
    
    def execute(self, state: GameState) -> dict:
        raise NotImplementedError

# commands/economy.py
class GainGoldCommand(Command):
    def __init__(self, player_id: str, amount: int):
        self.player_id = player_id
        self.amount = amount
    
    def get_entity_dependencies(self) -> List[str]:
        return [self.player_id]  # Затрагиваем только игрока
    
    def execute(self, state: GameState):
        # ... та же логика
```

### 5. Тесты конкурентности

```python
# tests/test_concurrency.py
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_gold_gain():
    """Тест: 100 параллельных команд GainGold"""
    state = GameState()
    state.set_entity("player1", {"gold": 0})
    
    executor = AsyncCommandExecutor(state)
    
    # 100 команд по +10 золота
    commands = [GainGoldCommand("player1", 10) for _ in range(100)]
    
    results = await asyncio.gather(*[
        executor.execute(cmd) for cmd in commands
    ])
    
    # Все команды успешны
    assert all(r.success for r in results)
    
    # Золото = 1000 (не потеряно ни одно изменение)
    assert state.get_entity("player1")["gold"] == 1000

@pytest.mark.asyncio
async def test_no_race_condition_in_combat():
    """Тест: два игрока атакуют одного моба"""
    state = GameState()
    state.set_entity("player1", {"attack": 10, "gold": 0})
    state.set_entity("player2", {"attack": 15, "gold": 0})
    state.set_entity("mob1", {"hp": 20, "gold_reward": 100})
    
    executor = AsyncCommandExecutor(state)
    
    # Оба игрока атакуют одновременно
    cmd1 = AttackMobCommand("player1", "mob1")
    cmd2 = AttackMobCommand("player2", "mob1")
    
    results = await asyncio.gather(
        executor.execute(cmd1),
        executor.execute(cmd2)
    )
    
    # Моб должен быть убит
    mob = state.get_entity("mob1")
    assert mob["hp"] <= 0
    
    # Награда не должна задублироваться!
    total_gold = (
        state.get_entity("player1")["gold"] + 
        state.get_entity("player2")["gold"]
    )
    assert total_gold == 100  # Ровно одна награда

@pytest.mark.asyncio
async def test_deadlock_prevention():
    """Тест: предотвращение deadlock при перекрёстных блокировках"""
    state = GameState()
    state.set_entity("player1", {"gold": 100})
    state.set_entity("player2", {"gold": 100})
    
    executor = AsyncCommandExecutor(state)
    
    # Команда которая затрагивает двух игроков
    class TradeCommand(Command):
        def __init__(self, from_id, to_id, amount):
            self.from_id = from_id
            self.to_id = to_id
            self.amount = amount
        
        def get_entity_dependencies(self):
            return [self.from_id, self.to_id]
        
        def execute(self, state):
            p1 = state.get_entity(self.from_id)
            p2 = state.get_entity(self.to_id)
            
            p1['gold'] -= self.amount
            p2['gold'] += self.amount
            
            state.set_entity(self.from_id, p1)
            state.set_entity(self.to_id, p2)
    
    # Перекрёстные транзакции
    cmd1 = TradeCommand("player1", "player2", 10)
    cmd2 = TradeCommand("player2", "player1", 20)
    
    # Не должно быть deadlock (таймаут 5 сек)
    results = await asyncio.wait_for(
        asyncio.gather(
            executor.execute(cmd1),
            executor.execute(cmd2)
        ),
        timeout=5.0
    )
    
    assert all(r.success for r in results)
```

## Критерии приёмки

- [ ] Транзакции работают (commit/rollback)
- [ ] Блокировки предотвращают race conditions
- [ ] Нет deadlocks при перекрёстных блокировках
- [ ] Все тесты конкурентности проходят
- [ ] 1000 параллельных команд выполняются корректно

## Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| Тест-покрытие | 100% |
| Race conditions в тестах | 0 |
| Deadlocks | 0 |
| Латентность команды (p99) | < 50ms |
| Throughput | > 100 команд/сек |

## Точки валидации

✅ **GO** если:
- 1000 параллельных команд не дают race conditions
- Нет deadlocks в stress-тестах (10 минут)
- Откат транзакции не оставляет артефактов

❌ **NO-GO** если:
- Появляются race conditions
- Deadlocks в нормальной нагрузке
- Производительность упала > 2x

---

# 🔄 Iteration 2: Data-Driven System

**Длительность:** 2 недели  
**Цель:** Вынести контент из кода в JSON

## Что делаем

### 1. JSON Schema для контента

```yaml
# data/schemas/mob_schema.yaml
type: object
required: [id, name, hp, attack, gold_reward]
properties:
  id:
    type: string
  name:
    type: string
  hp:
    type: integer
    minimum: 1
  attack:
    type: integer
    minimum: 0
  gold_reward:
    type: integer
    minimum: 0
  abilities:
    type: array
    items:
      type: object
      properties:
        id:
          type: string
        chance:
          type: number
          minimum: 0
          maximum: 1
```

### 2. Контент в JSON

```json
// data/mobs/goblin.json
{
  "id": "goblin_warrior",
  "name": "Goblin Warrior",
  "hp": 50,
  "attack": 8,
  "gold_reward": 25,
  "abilities": [
    {
      "id": "dodge",
      "chance": 0.2
    }
  ]
}

// data/mobs/boss_orc.json
{
  "id": "orc_chieftain",
  "name": "Orc Chieftain",
  "hp": 200,
  "attack": 25,
  "gold_reward": 500,
  "abilities": [
    {
      "id": "cleave",
      "chance": 0.3
    },
    {
      "id": "enrage",
      "chance": 0.1
    }
  ]
}
```

### 3. Data Loader

```python
# core/data_loader.py
import json
import yaml
from pathlib import Path
from typing import Dict, Any
from jsonschema import validate, ValidationError

class DataLoader:
    """Загрузчик и валидатор игровых данных"""
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.schemas = {}
        self.data = {}
    
    def load_schema(self, schema_name: str) -> dict:
        """Загрузить JSON Schema"""
        schema_path = self.data_dir / "schemas" / f"{schema_name}_schema.yaml"
        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def load_data(self, category: str, schema_name: str) -> Dict[str, Any]:
        """Загрузить все данные категории с валидацией"""
        if schema_name not in self.schemas:
            self.schemas[schema_name] = self.load_schema(schema_name)
        
        schema = self.schemas[schema_name]
        data_path = self.data_dir / category
        
        loaded = {}
        for json_file in data_path.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                item_data = json.load(f)
            
            # Валидация
            try:
                validate(instance=item_data, schema=schema)
            except ValidationError as e:
                raise ValueError(f"Invalid data in {json_file}: {e.message}")
            
            loaded[item_data['id']] = item_data
        
        return loaded
    
    def get(self, category: str, item_id: str) -> dict:
        """Получить конкретный элемент данных"""
        if category not in self.data:
            raise KeyError(f"Category {category} not loaded")
        
        return self.data[category].get(item_id)

# Глобальный загрузчик
data_loader = DataLoader()
data_loader.data['mobs'] = data_loader.load_data('mobs', 'mob')
```

### 4. Effect System

```json
// data/effects/fire_dot.json
{
  "id": "fire_dot",
  "name": "Burning",
  "type": "damage_over_time",
  "duration": 3,
  "tick_damage": 5,
  "stat_scaling": {
    "stat": "intelligence",
    "multiplier": 0.5
  }
}
```

```python
# core/effects.py
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class Effect:
    """Эффект (баф/дебаф)"""
    id: str
    name: str
    type: str
    duration: int
    properties: Dict[str, Any]
    
    @classmethod
    def from_data(cls, effect_data: dict):
        return cls(
            id=effect_data['id'],
            name=effect_data['name'],
            type=effect_data['type'],
            duration=effect_data['duration'],
            properties=effect_data
        )

class EffectResolver:
    """Интерпретатор эффектов"""
    def apply_effect(self, effect: Effect, target: dict, source: dict) -> dict:
        """Применить эффект к цели"""
        if effect.type == "damage_over_time":
            return self._apply_dot(effect, target, source)
        elif effect.type == "stat_modifier":
            return self._apply_stat_mod(effect, target)
        else:
            raise ValueError(f"Unknown effect type: {effect.type}")
    
    def _apply_dot(self, effect: Effect, target: dict, source: dict) -> dict:
        base_damage = effect.properties['tick_damage']
        
        # Scaling от характеристики источника
        if 'stat_scaling' in effect.properties:
            scaling = effect.properties['stat_scaling']
            stat_value = source.get(scaling['stat'], 0)
            base_damage += stat_value * scaling['multiplier']
        
        target['hp'] -= base_damage
        
        return {
            "damage_dealt": base_damage,
            "target_hp": target['hp']
        }
    
    def _apply_stat_mod(self, effect: Effect, target: dict) -> dict:
        stat = effect.properties['stat']
        modifier = effect.properties['modifier']
        
        if stat not in target:
            target[stat] = 0
        
        target[stat] += modifier
        
        return {"stat": stat, "new_value": target[stat]}
```

### 5. Data-Driven Combat

```python
# commands/combat.py
from core.data_loader import data_loader
from core.effects import Effect, EffectResolver

class AttackMobCommand(Command):
    def __init__(self, player_id: str, mob_id: str):
        self.player_id = player_id
        self.mob_id = mob_id
    
    def get_entity_dependencies(self):
        return [self.player_id, self.mob_id]
    
    def execute(self, state: GameState):
        player = state.get_entity(self.player_id)
        mob = state.get_entity(self.mob_id)
        
        # Мобы теперь из данных!
        mob_template = data_loader.get('mobs', mob['template_id'])
        
        # Базовый урон
        damage = player.get('attack', 10)
        
        # Проверка способностей моба
        import random
        for ability in mob_template.get('abilities', []):
            if random.random() < ability['chance']:
                if ability['id'] == 'dodge':
                    damage = 0  # Уклонение
                elif ability['id'] == 'cleave':
                    damage *= 1.5  # Усиленная атака
        
        mob['hp'] -= damage
        
        # Награда при убийстве
        result = {
            "damage_dealt": damage,
            "mob_hp": mob['hp'],
            "mob_killed": False
        }
        
        if mob['hp'] <= 0:
            player['gold'] += mob_template['gold_reward']
            result['mob_killed'] = True
            result['gold_gained'] = mob_template['gold_reward']
        
        state.set_entity(self.player_id, player)
        state.set_entity(self.mob_id, mob)
        
        return result
```

### 6. Тесты Data-Driven

```python
# tests/test_data_driven.py
def test_data_loader_validation():
    """Невалидные данные должны отклоняться"""
    loader = DataLoader("tests/fixtures")
    
    # Создаём невалидный JSON (отрицательный HP)
    invalid_mob = {
        "id": "invalid",
        "name": "Invalid",
        "hp": -10,  # Нарушает schema
        "attack": 5,
        "gold_reward": 10
    }
    
    with pytest.raises(ValueError, match="Invalid data"):
        loader.validate_item(invalid_mob, 'mob')

def test_mob_from_data():
    """Мобы создаются из JSON"""
    goblin_data = data_loader.get('mobs', 'goblin_warrior')
    
    assert goblin_data['name'] == "Goblin Warrior"
    assert goblin_data['hp'] == 50
    assert len(goblin_data['abilities']) > 0

def test_effect_system():
    """Эффекты применяются через интерпретатор"""
    effect_data = {
        "id": "burn",
        "name": "Burning",
        "type": "damage_over_time",
        "duration": 3,
        "tick_damage": 5
    }
    
    effect = Effect.from_data(effect_data)
    resolver = EffectResolver()
    
    target = {"hp": 100}
    source = {}
    
    result = resolver.apply_effect(effect, target, source)
    
    assert target['hp'] == 95
    assert result['damage_dealt'] == 5
```

## Критерии приёмки

- [ ] Все мобы вынесены в JSON
- [ ] Валидация данных работает
- [ ] Effect system обрабатывает 5+ типов эффектов
- [ ] Можно добавить нового моба БЕЗ изменения кода
- [ ] Все тесты проходят

## Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| % контента в JSON | > 90% |
| Время загрузки данных | < 100ms |
| Количество if-else для контента | 0 |
| Скорость добавления нового моба | < 5 минут |

## Точки валидации

✅ **GO** если:
- Новый моб добавляется через JSON за 5 минут
- Невалидные данные отклоняются при загрузке
- Нет хардкода контента в коде

❌ **NO-GO** если:
- Приходится менять код для нового контента
- Валидация пропускает невалидные данные
- Производительность загрузки > 500ms

---

# 🔄 Iteration 3: Event System

**Длительность:** 1.5 недели  
**Цель:** Добавить реактивность и декаплинг модулей

## Что делаем

### 1. Event Bus

```python
# core/events.py
from typing import Callable, List, Dict, Type
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Event:
    """Базовое событие"""
    timestamp: datetime
    event_type: str
    data: dict

class PlayerLevelUpEvent(Event):
    def __init__(self, player_id: str, new_level: int):
        super().__init__(
            timestamp=datetime.now(),
            event_type="player_level_up",
            data={"player_id": player_id, "level": new_level}
        )

class MobKilledEvent(Event):
    def __init__(self, player_id: str, mob_id: str, mob_template: str):
        super().__init__(
            timestamp=datetime.now(),
            event_type="mob_killed",
            data={
                "player_id": player_id,
                "mob_id": mob_id,
                "mob_template": mob_template
            }
        )

class EventBus:
    """Шина событий"""
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        """Подписаться на тип события"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def publish(self, event: Event):
        """Опубликовать событие"""
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Ошибка в одном подписчике не должна ломать других
                print(f"Error in event handler: {e}")
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """Отписаться от события"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)

# Глобальная шина
event_bus = EventBus()
```

### 2. Модульная архитектура через события

```python
# modules/achievements.py
from core.events import event_bus, MobKilledEvent

class AchievementModule:
    """Модуль достижений (не знает про Combat!)"""
    def __init__(self, state: GameState):
        self.state = state
        
        # Подписываемся на события
        event_bus.subscribe("mob_killed", self.on_mob_killed)
    
    def on_mob_killed(self, event: MobKilledEvent):
        """Реакция на убийство моба"""
        player_id = event.data['player_id']
        mob_template = event.data['mob_template']
        
        player = self.state.get_entity(player_id)
        
        if 'achievements' not in player:
            player['achievements'] = {}
        
        # Прогресс достижения "Убить 10 гоблинов"
        if mob_template == "goblin_warrior":
            key = "goblin_slayer"
            player['achievements'][key] = player['achievements'].get(key, 0) + 1
            
            if player['achievements'][key] == 10:
                # Выдать награду
                player['gold'] += 1000
                event_bus.publish(Event(
                    timestamp=datetime.now(),
                    event_type="achievement_unlocked",
                    data={"player_id": player_id, "achievement": key}
                ))
        
        self.state.set_entity(player_id, player)

# modules/progression.py
class ProgressionModule:
    """Модуль прогрессии"""
    def __init__(self, state: GameState):
        self.state = state
        event_bus.subscribe("mob_killed", self.on_mob_killed)
    
    def on_mob_killed(self, event: MobKilledEvent):
        """Начисление опыта за убийство"""
        player_id = event.data['player_id']
        mob_template = event.data['mob_template']
        
        # Опыт из данных моба
        mob_data = data_loader.get('mobs', mob_template)
        exp = mob_data.get('exp_reward', 10)
        
        player = self.state.get_entity(player_id)
        player['exp'] = player.get('exp', 0) + exp
        
        # Проверка levelup
        exp_needed = player.get('level', 1) * 100
        if player['exp'] >= exp_needed:
            player['level'] = player.get('level', 1) + 1
            player['exp'] = 0
            
            event_bus.publish(PlayerLevelUpEvent(
                player_id=player_id,
                new_level=player['level']
            ))
        
        self.state.set_entity(player_id, player)
```

### 3. Обновление команд для публикации событий

```python
# commands/combat.py
class AttackMobCommand(Command):
    def execute(self, state: GameState):
        # ... логика боя
        
        if mob['hp'] <= 0:
            # Публикуем событие
            event_bus.publish(MobKilledEvent(
                player_id=self.player_id,
                mob_id=self.mob_id,
                mob_template=mob['template_id']
            ))
        
        return result
```

### 4. Тесты событий

```python
# tests/test_events.py
def test_event_publishing():
    """События публикуются и доставляются подписчикам"""
    bus = EventBus()
    
    received_events = []
    
    def handler(event):
        received_events.append(event)
    
    bus.subscribe("test_event", handler)
    
    event = Event(
        timestamp=datetime.now(),
        event_type="test_event",
        data={"foo": "bar"}
    )
    
    bus.publish(event)
    
    assert len(received_events) == 1
    assert received_events[0].data['foo'] == "bar"

def test_module_independence():
    """Модули не знают друг о друге, общаются через события"""
    state = GameState()
    state.set_entity("player1", {"gold": 0, "exp": 0, "level": 1})
    
    # Подключаем модули
    achievements = AchievementModule(state)
    progression = ProgressionModule(state)
    
    # Убиваем 10 гоблинов
    for i in range(10):
        event_bus.publish(MobKilledEvent(
            player_id="player1",
            mob_id=f"mob{i}",
            mob_template="goblin_warrior"
        ))
    
    player = state.get_entity("player1")
    
    # Progression модуль начислил опыт
    assert player['exp'] > 0 or player['level'] > 1
    
    # Achievement модуль выдал награду
    assert player['gold'] == 1000
    assert player['achievements']['goblin_slayer'] == 10

def test_error_in_one_handler_does_not_break_others():
    """Ошибка в одном подписчике не ломает других"""
    bus = EventBus()
    
    results = []
    
    def failing_handler(event):
        raise ValueError("Boom!")
    
    def working_handler(event):
        results.append("success")
    
    bus.subscribe("test", failing_handler)
    bus.subscribe("test", working_handler)
    
    event = Event(datetime.now(), "test", {})
    bus.publish(event)
    
    # Второй обработчик сработал несмотря на ошибку первого
    assert len(results) == 1
    assert results[0] == "success"
```

## Критерии приёмки

- [ ] Event Bus реализован
- [ ] 2+ модуля общаются через события
- [ ] Модули не имеют прямых зависимостей друг от друга
- [ ] Ошибка в одном подписчике не ломает других
- [ ] Все тесты проходят

## Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| Связность модулей (coupling) | < 10% |
| Количество прямых import между модулями | 0 |
| Event delivery latency | < 1ms |
| Fault isolation | 100% |

## Точки валидации

✅ **GO** если:
- Новый модуль добавляется без изменения существующих
- События доставляются всем подписчикам
- Ошибка в подписчике изолирована

❌ **NO-GO** если:
- Модули напрямую зависят друг от друга
- События теряются
- Ошибка в одном подписчике ломает всю систему

---

# 🔄 Iteration 4: Persistence Layer

**Длительность:** 2 недели  
**Цель:** Сохранение состояния в БД

## Что делаем

### 1. Repository Pattern

```python
# core/repository.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class EntityRepository(ABC):
    """Абстрактный репозиторий сущностей"""
    
    @abstractmethod
    def save(self, entity_id: str, entity_data: dict):
        """Сохранить сущность"""
        pass
    
    @abstractmethod
    def load(self, entity_id: str) -> Optional[dict]:
        """Загрузить сущность"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str):
        """Удалить сущность"""
        pass
    
    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Проверить существование"""
        pass
```

### 2. SQLite Implementation

```python
# adapters/sqlite_repository.py
import sqlite3
import json
from typing import Optional

class SQLiteRepository(EntityRepository):
    """Репозиторий на базе SQLite"""
    
    def __init__(self, db_path: str = "game.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Создать таблицы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                data TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_type 
            ON entities(entity_type)
        """)
        
        conn.commit()
        conn.close()
    
    def save(self, entity_id: str, entity_data: dict):
        """Сохранить с оптимистичными блокировками"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        entity_type = entity_data.get('_type', 'unknown')
        data_json = json.dumps(entity_data)
        current_version = entity_data.get('_version', 1)
        
        # Оптимистичная блокировка через версию
        cursor.execute("""
            INSERT INTO entities (entity_id, entity_type, data, version)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                data = excluded.data,
                version = version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE version = ?
        """, (entity_id, entity_type, data_json, current_version, current_version))
        
        if cursor.rowcount == 0:
            raise ValueError(f"Optimistic lock failed for {entity_id}")
        
        conn.commit()
        conn.close()
    
    def load(self, entity_id: str) -> Optional[dict]:
        """Загрузить сущность"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT data, version FROM entities WHERE entity_id = ?
        """, (entity_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        data = json.loads(row[0])
        data['_version'] = row[1]
        return data
    
    def delete(self, entity_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entities WHERE entity_id = ?", (entity_id,))
        conn.commit()
        conn.close()
    
    def exists(self, entity_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM entities WHERE entity_id = ? LIMIT 1",
            (entity_id,)
        )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
```

### 3. Persistent State Manager

```python
# core/persistent_state.py
class PersistentGameState(GameState):
    """State с автоматическим сохранением"""
    
    def __init__(self, repository: EntityRepository):
        super().__init__()
        self.repository = repository
        self._dirty_entities = set()
    
    def get_entity(self, entity_id: str) -> dict:
        """Загрузить из памяти или БД"""
        if entity_id not in self._entities:
            # Ленивая загрузка из БД
            data = self.repository.load(entity_id)
            if data:
                self._entities[entity_id] = data
        
        return self._entities.get(entity_id)
    
    def set_entity(self, entity_id: str, data: dict):
        """Пометить как изменённую"""
        self._entities[entity_id] = data
        self._dirty_entities.add(entity_id)
    
    def flush(self):
        """Сохранить все изменённые сущности"""
        for entity_id in self._dirty_entities:
            entity_data = self._entities[entity_id]
            self.repository.save(entity_id, entity_data)
        
        self._dirty_entities.clear()
```

### 4. Transaction with Persistence

```python
# core/transaction.py (обновлённая версия)
class PersistentTransaction(Transaction):
    """Транзакция с сохранением в БД"""
    
    def __init__(self, state: PersistentGameState):
        super().__init__(state)
        self.persistent_state = state
    
    def commit(self):
        """Применить изменения и сохранить в БД"""
        if self._committed:
            raise RuntimeError("Transaction already committed")
        
        # Сначала в память
        self._original_state._entities = self._snapshot
        
        # Потом в БД (атомарно)
        try:
            self.persistent_state.flush()
            self._committed = True
        except Exception as e:
            # Откат в памяти
            self._snapshot = deepcopy(self._original_state._entities)
            raise RuntimeError(f"Failed to persist transaction: {e}")
```

### 5. Тесты персистентности

```python
# tests/test_persistence.py
import tempfile
import os

def test_save_and_load():
    """Данные сохраняются и загружаются корректно"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = SQLiteRepository(db_path)
        
        # Сохранить
        player_data = {
            "_type": "player",
            "gold": 100,
            "level": 5
        }
        repo.save("player1", player_data)
        
        # Загрузить
        loaded = repo.load("player1")
        
        assert loaded['gold'] == 100
        assert loaded['level'] == 5

def test_optimistic_locking():
    """Оптимистичные блокировки предотвращают конфликты"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = SQLiteRepository(db_path)
        
        # Сохранить v1
        data_v1 = {"_type": "player", "gold": 100, "_version": 1}
        repo.save("player1", data_v1)
        
        # Загрузить в два "потока"
        thread1_data = repo.load("player1")
        thread2_data = repo.load("player1")
        
        # Thread 1 изменяет
        thread1_data['gold'] = 200
        repo.save("player1", thread1_data)
        
        # Thread 2 пытается изменить устаревшую версию
        thread2_data['gold'] = 150
        
        with pytest.raises(ValueError, match="Optimistic lock failed"):
            repo.save("player1", thread2_data)

def test_transaction_persistence():
    """Транзакция сохраняется в БД только при commit"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = SQLiteRepository(db_path)
        
        state = PersistentGameState(repo)
        state.set_entity("player1", {
            "_type": "player",
            "gold": 100,
            "_version": 1
        })
        state.flush()
        
        # Выполнить команду в транзакции
        executor = TransactionalExecutor(state)
        cmd = GainGoldCommand("player1", 50)
        result = executor.execute(cmd)
        
        assert result.success
        
        # Проверить что данные в БД
        loaded = repo.load("player1")
        assert loaded['gold'] == 150
```

## Критерии приёмки

- [ ] Repository pattern реализован
- [ ] SQLite адаптер работает
- [ ] Оптимистичные блокировки предотвращают конфликты
- [ ] Транзакции сохраняются атомарно
- [ ] Все тесты проходят

## Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| Время сохранения сущности | < 10ms |
| Конфликты оптимистичных блокировок | < 1% |
| Успешность восстановления после краша | 100% |
| Data loss | 0 |

## Точки валидации

✅ **GO** если:
- Данные сохраняются и загружаются корректно
- Нет потери данных при крашах
- Оптимистичные блокировки работают

❌ **NO-GO** если:
- Происходит потеря данных
- Частые конфликты блокировок (> 5%)
- Производительность сохранения > 50ms

---

# 🔄 Iteration 5: Telegram Adapter

**Длительность:** 2 недели  
**Цель:** Подключить Telegram как UI-клиент

## Что делаем

### 1. Command Adapter

```python
# adapters/telegram/command_adapter.py
from aiogram import types
from core.command import Command
from commands.economy import GainGoldCommand, SpendGoldCommand
from commands.combat import AttackMobCommand

class TelegramCommandAdapter:
    """Адаптер Telegram → Commands"""
    
    def __init__(self, executor: AsyncCommandExecutor):
        self.executor = executor
    
    async def handle_callback(self, callback: types.CallbackQuery) -> CommandResult:
        """Преобразовать callback в команду"""
        user_id = str(callback.from_user.id)
        data = callback.data
        
        # Парсинг callback_data
        if data.startswith("attack:"):
            mob_id = data.split(":")[1]
            command = AttackMobCommand(user_id, mob_id)
        
        elif data.startswith("buy:"):
            item_id = data.split(":")[1]
            item_data = data_loader.get('items', item_id)
            command = SpendGoldCommand(user_id, item_data['price'])
        
        else:
            raise ValueError(f"Unknown callback: {data}")
        
        # Выполнить команду
        result = await self.executor.execute(command)
        return result
    
    async def handle_command(self, message: types.Message) -> CommandResult:
        """Преобразовать текстовую команду"""
        user_id = str(message.from_user.id)
        text = message.text
        
        if text == "/claim_daily":
            command = GainGoldCommand(user_id, 100)
        
        else:
            raise ValueError(f"Unknown command: {text}")
        
        result = await self.executor.execute(command)
        return result
```

### 2. Response Builder

```python
# adapters/telegram/response_builder.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class ResponseBuilder:
    """Строитель ответов для Telegram"""
    
    def build_combat_result(self, result: CommandResult) -> dict:
        """Ответ на результат боя"""
        if not result.success:
            return {
                "text": f"❌ Ошибка: {result.error}",
                "reply_markup": None
            }
        
        data = result.data
        
        text = f"⚔️ Вы нанесли {data['damage_dealt']} урона!\n"
        
        if data['mob_killed']:
            text += f"💀 Моб убит!\n💰 Получено: {data.get('gold_gained', 0)} золота"
            keyboard = None
        else:
            text += f"❤️ HP моба: {data['mob_hp']}"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⚔️ Атаковать ещё",
                    callback_data=f"attack:{data['mob_id']}"
                )]
            ])
        
        return {
            "text": text,
            "reply_markup": keyboard
        }
    
    def build_player_stats(self, player_data: dict) -> dict:
        """Статистика игрока"""
        text = (
            f"👤 Профиль\n"
            f"💰 Золото: {player_data.get('gold', 0)}\n"
            f"⭐ Уровень: {player_data.get('level', 1)}\n"
            f"🎯 Опыт: {player_data.get('exp', 0)}\n"
        )
        
        return {"text": text, "reply_markup": None}
```

### 3. Bot Integration

```python
# adapters/telegram/bot.py
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio

class GameBot:
    """Telegram бот"""
    
    def __init__(self, token: str, executor: AsyncCommandExecutor):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.executor = executor
        self.adapter = TelegramCommandAdapter(executor)
        self.response_builder = ResponseBuilder()
        
        # Регистрация хендлеров
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.dp.message(Command("start"))
        async def start_handler(message: types.Message):
            user_id = str(message.from_user.id)
            
            # Создать игрока если не существует
            if not state.get_entity(user_id):
                state.set_entity(user_id, {
                    "_type": "player",
                    "gold": 0,
                    "level": 1,
                    "exp": 0,
                    "attack": 10
                })
                state.flush()
            
            await message.answer(
                "🎮 Добро пожаловать в игру!\n"
                "Используйте /fight чтобы сразиться с мобом"
            )
        
        @self.dp.message(Command("fight"))
        async def fight_handler(message: types.Message):
            user_id = str(message.from_user.id)
            
            # Создать моба
            mob_id = f"mob_{user_id}_{int(time.time())}"
            state.set_entity(mob_id, {
                "_type": "mob",
                "template_id": "goblin_warrior",
                "hp": 50
            })
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⚔️ Атаковать",
                    callback_data=f"attack:{mob_id}"
                )]
            ])
            
            await message.answer(
                "👹 Перед вами Goblin Warrior!\n❤️ HP: 50",
                reply_markup=keyboard
            )
        
        @self.dp.callback_query()
        async def callback_handler(callback: types.CallbackQuery):
            result = await self.adapter.handle_callback(callback)
            response = self.response_builder.build_combat_result(result)
            
            await callback.message.edit_text(
                text=response['text'],
                reply_markup=response['reply_markup']
            )
            await callback.answer()
    
    async def start(self):
        """Запустить бота"""
        await self.dp.start_polling(self.bot)
```

### 4. Тесты адаптера

```python
# tests/test_telegram_adapter.py
from unittest.mock import Mock, AsyncMock
import pytest

@pytest.mark.asyncio
async def test_callback_to_command():
    """Callback преобразуется в команду"""
    executor = Mock()
    executor.execute = AsyncMock(return_value=CommandResult(
        success=True,
        data={"damage_dealt": 10, "mob_hp": 40, "mob_killed": False}
    ))
    
    adapter = TelegramCommandAdapter(executor)
    
    callback = Mock()
    callback.from_user.id = 12345
    callback.data = "attack:mob_1"
    
    result = await adapter.handle_callback(callback)
    
    assert result.success
    assert executor.execute.called
    
    # Проверить что создана правильная команда
    called_command = executor.execute.call_args[0][0]
    assert isinstance(called_command, AttackMobCommand)
    assert called_command.player_id == "12345"
    assert called_command.mob_id == "mob_1"

def test_response_builder_combat():
    """Response builder создаёт правильный ответ"""
    builder = ResponseBuilder()
    
    result = CommandResult(
        success=True,
        data={
            "damage_dealt": 15,
            "mob_hp": 0,
            "mob_killed": True,
            "gold_gained": 50
        }
    )
    
    response = builder.build_combat_result(result)
    
    assert "15 урона" in response['text']
    assert "Моб убит" in response['text']
    assert "50 золота" in response['text']
    assert response['reply_markup'] is None  # Моб мёртв, кнопок нет
```

## Критерии приёмки

- [ ] Telegram бот запускается
- [ ] Callback превращаются в команды
- [ ] Результаты команд превращаются в UI
- [ ] Можно сыграть простой бой через Telegram
- [ ] Все тесты проходят

## Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| Response time | < 500ms |
| Успешность обработки callback | > 99% |
| Crash rate | < 0.1% |
| User retention (Day 1) | > 40% |

## Точки валидации

✅ **GO** если:
- Бот отвечает на команды
- UI понятен пользователю
- Нет крашей при обычном использовании

❌ **NO-GO** если:
- Бот не отвечает / долго думает
- UI непонятен
- Частые краши

---

# 🔄 Iteration 6: First Playable Game

**Длительность:** 3 недели  
**Цель:** Полная играбельная RPG

## Что делаем

### 1. Полный набор контента

```json
// data/mobs/ - 10+ мобов разной сложности
// data/items/ - 20+ предметов
// data/skills/ - 5+ скиллов игрока
// data/locations/ - 3+ локации
```

### 2. Дополнительные механики

- **Inventory System** — экипировка, расходники
- **Quest System** — простые квесты
- **Shop System** — покупка/продажа
- **Skill System** — активные способности

### 3. Прогрессия

- Левелинг (1-20)
- Разблокировка локаций
- Улучшение снаряжения

### 4. Балансировка

- Кривая сложности
- Экономический баланс
- Reward pacing

### 5. Polishing

- Красивые тексты
- Эмодзи и форматирование
- Туториал для новых игроков

## Критерии приёмки

- [ ] 30+ минут геймплея без повторений
- [ ] Понятный tutorial
- [ ] Сбалансированная экономика
- [ ] 0 критических багов
- [ ] 10 альфа-тестеров прошли игру

## Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| Session length | > 15 минут |
| Day 1 retention | > 50% |
| Day 7 retention | > 20% |
| Tutorial completion | > 80% |
| Crash-free sessions | > 99% |

## Точки валидации

✅ **GO** если:
- Игра "залипает" на 30+ минут
- Альфа-тестеры довольны
- Баланс не сломан
- Технически стабильно

❌ **NO-GO** если:
- Игра скучная / непонятная
- Баланс сломан (слишком легко/сложно)
- Много критических багов

---

# 🔄 Iteration 7: Engine Extraction

**Длительность:** 2 недели  
**Цель:** Выделить переиспользуемое в движок

## Что делаем

### 1. Анализ кодовой базы

- Что специфично для игры?
- Что универсально?
- Какие интерфейсы нужны?

### 2. Рефакторинг

```
game/
├── engine/          # Переиспользуемое
│   ├── core/
│   ├── modules/
│   └── adapters/
└── my_rpg/          # Специфика игры
    ├── data/
    ├── custom_commands/
    └── config.py
```

### 3. Plugin API

```python
# engine/plugin.py
class GamePlugin:
    """Интерфейс плагина игры"""
    
    def register_commands(self, registry: CommandRegistry):
        """Зарегистрировать команды"""
        pass
    
    def register_events(self, bus: EventBus):
        """Подписаться на события"""
        pass
    
    def register_data(self, loader: DataLoader):
        """Зарегистрировать типы данных"""
        pass
```

### 4. Документация движка

- Architecture guide
- API reference
- Tutorial "Create your first game"
- Best practices

### 5. CLI для генерации проектов

```bash
$ game-engine create my-game --template=rpg
Creating new game: my-game
✓ Project structure created
✓ Sample data generated
✓ Config initialized

Next steps:
  cd my-game
  python bot.py
```

## Критерии приёмки

- [ ] Движок отделён от игры
- [ ] Plugin API документирован
- [ ] Можно создать новую игру за 1 час
- [ ] Примеры для каждого модуля
- [ ] CLI генератор работает

## Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| Время создания новой игры | < 1 час |
| % кода в движке | > 70% |
| Документация coverage | > 90% |
| External contributors | > 0 |

---

# 🔄 Iteration 8: Second Game (Validation)

**Длительность:** 2-3 недели  
**Цель:** Проверить универсальность движка

## Что делаем

### Создать ДРУГУЮ игру на том же движке

Например: **Idle Farm Simulator**

- Автофарм ресурсов
- Апгрейды зданий
- Без боёвки
- Без мобов

### Использовать ТОЛЬКО публичный API движка

Запрещено:
- Лезть в внутренности движка
- Менять ядро
- Хаки и workarounds

### Зафиксировать болевые точки

- Что не хватает в API?
- Что неудобно?
- Что пришлось делать костылями?

### Улучшить движок на основе опыта

## Критерии приёмки

- [ ] Вторая игра создана БЕЗ изменений ядра движка
- [ ] 0 хаков / workarounds
- [ ] Обе игры работают на одной версии движка
- [ ] Движок стал лучше после feedback

## Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| Время разработки второй игры | < 50% первой |
| % кода переиспользуемого | > 80% |
| Количество улучшений движка | > 5 |
| API breaking changes | 0 |

## Точки валидации

✅ **GO** если:
- Вторая игра создаётся легко
- Не нужно менять ядро
- API покрывает use cases

❌ **NO-GO** если:
- Постоянно приходится менять ядро
- Много хаков
- API недостаточно

---

# 🔄 Iteration 9: Production Hardening

**Длительность:** 2-3 недели  
**Цель:** Подготовка к production

## Что делаем

### 1. Monitoring & Observability

```python
# observability/metrics.py
from prometheus_client import Counter, Histogram

command_counter = Counter(
    'game_commands_total',
    'Total commands executed',
    ['command_type', 'status']
)

command_duration = Histogram(
    'game_command_duration_seconds',
    'Command execution time',
    ['command_type']
)

# В executor
@observe_metrics
async def execute(self, command):
    start = time.time()
    try:
        result = await super().execute(command)
        command_counter.labels(
            command_type=type(command).__name__,
            status='success'
        ).inc()
        return result
    except Exception as e:
        command_counter.labels(
            command_type=type(command).__name__,
            status='error'
        ).inc()
        raise
    finally:
        duration = time.time() - start
        command_duration.labels(
            command_type=type(command).__name__
        ).observe(duration)
```

### 2. Error Tracking

```python
# Sentry integration
import sentry_sdk

sentry_sdk.init(
    dsn="...",
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1
)

# Автоматический трекинг ошибок
@sentry_sdk.trace
async def execute_command(cmd):
    ...
```

### 3. Graceful Shutdown

```python
# Корректное завершение
class GracefulShutdown:
    def __init__(self, executor):
        self.executor = executor
        self.shutting_down = False
    
    async def shutdown(self):
        self.shutting_down = True
        
        # Дождаться завершения команд
        await self.executor.wait_for_completion()
        
        # Сохранить state
        await self.executor.state.flush()
        
        # Закрыть соединения
        await self.executor.close()
```

### 4. Rate Limiting

```python
# Защита от спама
class RateLimiter:
    def __init__(self, max_commands_per_minute=20):
        self.max_cpm = max_commands_per_minute
        self.user_counters = {}
    
    async def check(self, user_id: str):
        now = time.time()
        
        if user_id not in self.user_counters:
            self.user_counters[user_id] = []
        
        # Очистить старые
        self.user_counters[user_id] = [
            t for t in self.user_counters[user_id]
            if now - t < 60
        ]
        
        if len(self.user_counters[user_id]) >= self.max_cpm:
            raise RateLimitError("Too many requests")
        
        self.user_counters[user_id].append(now)
```

### 5. Backups

```python
# Автобэкапы
class BackupManager:
    async def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backups/game_{timestamp}.db"
        
        # Копировать БД
        shutil.copy("game.db", backup_path)
        
        # Сжать
        with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
            with open(backup_path, 'rb') as f_in:
                f_out.writelines(f_in)
        
        os.remove(backup_path)
        
        # Очистить старые (оставить последние 7 дней)
        self.cleanup_old_backups(days=7)
```

### 6. Load Testing

```python
# tests/load_test.py
import asyncio
from locust import User, task, between

class GameUser(User):
    wait_time = between(1, 5)
    
    @task(3)
    def attack_mob(self):
        self.client.post("/command", json={
            "type": "attack",
            "mob_id": "goblin_1"
        })
    
    @task(1)
    def check_stats(self):
        self.client.get("/stats")

# Запуск: locust -f load_test.py --users 1000 --spawn-rate 10
```

## Критерии приёмки

- [ ] Monitoring настроен (Prometheus/Grafana)
- [ ] Error tracking работает (Sentry)
- [ ] Graceful shutdown корректен
- [ ] Rate limiting защищает от спама
- [ ] Автобэкапы каждые 6 часов
- [ ] Load test: 1000 CCU без деградации

## Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| Uptime | > 99.9% |
| p99 latency под нагрузкой | < 200ms |
| Error rate | < 0.1% |
| Time to recovery | < 5 минут |
| Backup success rate | 100% |

---

## Стратегия тестирования

### Unit Tests

```python
# Каждая команда
# Каждый модуль
# Каждый эффект
# Coverage > 90%
```

### Integration Tests

```python
# Полные флоу (регистрация → бой → levelup)
# Взаимодействие модулей через события
# Персистентность
```

### Concurrency Tests

```python
# Race conditions
# Deadlocks
# Stress tests (1000 параллельных команд)
```

### End-to-End Tests

```python
# Реальные сценарии пользователей
# Через Telegram API
# Selenium для Web-версии (если есть)
```

### Load Tests

```python
# 100 CCU
# 1000 CCU
# 10000 CCU (целевая)
```

### Chaos Engineering

```python
# Убить БД во время транзакции
# Отключить сеть
# Перегрузить CPU
# Заполнить диск
```

---

## Критерии успеха

### Технические метрики

| Метрика | Iteration 0 | Iteration 3 | Iteration 6 | Iteration 9 |
|---------|-------------|-------------|-------------|-------------|
| Test Coverage | 100% | 95% | 90% | 95% |
| Response Time (p99) | 1ms | 10ms | 50ms | 100ms |
| Throughput | 10K cmd/s | 1K cmd/s | 100 cmd/s | 500 cmd/s |
| Uptime | N/A | N/A | 95% | 99.9% |
| Error Rate | 0% | < 1% | < 0.5% | < 0.1% |

### Продуктовые метрики

| Метрика | Iteration 6 | Iteration 8 | Iteration 9 |
|---------|-------------|-------------|-------------|
| DAU | 10 | 100 | 1000 |
| Session Length | 15 min | 20 min | 25 min |
| D1 Retention | 50% | 60% | 70% |
| D7 Retention | 20% | 30% | 40% |

---

## Управление рисками

### Risk Matrix

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Over-engineering | Высокая | Среднее | Начать с конкретной игры |
| Performance issues | Средняя | Высокое | Бенчмарки на каждой итерации |
| Сложность для разработчиков | Средняя | Высокое | Документация + примеры |
| Scope creep | Высокая | Высокое | Жёсткие критерии приёмки |
| Technical debt | Средняя | Среднее | Рефакторинг на Iteration 7 |

### Точки отката

После каждой итерации:
- Если валидация провалена → откат к предыдущей
- Если нужно переосмыслить архитектуру → spike решения
- Если блокер → приоритизация фикса

---

## Заключение

Эта методология обеспечивает:

✅ **Контролируемый риск** — каждая итерация тестируема  
✅ **Быструю обратную связь** — валидация после каждого шага  
✅ **Гибкость** — можно остановиться на любом этапе  
✅ **Измеримость** — чёткие метрики успеха

**Главное правило:** 
> Лучше иметь рабочую простую версию,  
> чем сложную нерабочую.

Вперёд к созданию движка! 🚀
