# 🎮 Telegram Game Engine

**Production-ready игровой движок для Telegram-ботов с command-based архитектурой**

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.6.0-blue.svg)](setup.py)
[![Tests](https://img.shields.io/badge/tests-196%20passed-success.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-89.76%25-brightgreen.svg)](htmlcov/index.html)

---

## 📖 Что это?

**Telegram Game Engine** — это production-ready фреймворк для создания игровых Telegram-ботов любых жанров: RPG, idle-clicker, gacha, roguelike и других.

### 🎯 Главные преимущества

- ✅ **Без race conditions** — автоматическая изоляция конкурентных операций
- ✅ **ACID гарантии** — транзакционность и откат при ошибках
- ✅ **Data-driven** — весь контент в JSON, без изменения кода
- ✅ **Event-driven** — реактивная система событий
- ✅ **Готовые шаблоны** — RPG, Idle Clicker, Card Game
- ✅ **100% документация** — QuickStart + API Reference + примеры

---

## 🚀 Быстрый старт

### 1. Использовать готовый шаблон (рекомендуется)

```bash
# Скопировать шаблон
cp -r templates/rpg my_rpg_game
cd my_rpg_game

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить движок
pip install -e path/to/tg_bot_engine
pip install -r requirements.txt

# Настроить токен
cp .env.example .env
# Добавьте TELEGRAM_BOT_TOKEN в .env

# Запустить
python bot.py
```

### 2. Создать с нуля

Следуйте **[QUICKSTART.md](docs/QUICKSTART.md)** для пошагового создания игры за 30 минут.

---

## 🎨 Готовые шаблоны

| Шаблон | Описание | Время разработки |
|--------|----------|-----------------|
| **🎮 RPG** | Turn-based RPG с боями, инвентарём, квестами | 2-4 недели |
| **🏭 Idle Clicker** | Инкрементальная игра с автопроизводством | 1-2 недели |
| **🃏 Card Game** | Карточная игра с коллекцией и сражениями | 3-5 недель |

📖 Подробнее: см. README.md в каждой папке `templates/`

---

## 💡 Простой пример

```python
from engine.core import PersistentGameState, CommandExecutor
from engine.adapters import SQLiteRepository
from engine.commands.combat import AttackMobCommand

# Создать состояние с автосохранением
repo = SQLiteRepository("game.db")
state = PersistentGameState(repo, auto_flush=True)
executor = CommandExecutor()

# Создать игрока и моба
state.set_entity("player_1", {
    "_type": "player",
    "gold": 100,
    "attack": 10
})

state.set_entity("mob_1", {
    "_type": "mob",
    "hp": 50,
    "template_id": "goblin"
})

# Атаковать
cmd = AttackMobCommand("player_1", "mob_1")
result = executor.execute(cmd, state)

if result.success:
    print(f"Урон: {result.data['damage_dealt']}")
    print(f"HP моба: {result.data['mob_hp']}")
    if result.data['mob_killed']:
        print(f"Моб убит! +{result.data['gold_gained']} золота")
```

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────┐
│     TELEGRAM BOT (UI слой)              │
├─────────────────────────────────────────┤
│     ADAPTER (Telegram → Commands)       │
├─────────────────────────────────────────┤
│     COMMANDS (Бизнес-логика)            │
├─────────────────────────────────────────┤
│     ENGINE CORE                         │
│  • Command Executor                     │
│  • State Manager                        │
│  • Event System                         │
│  • Transaction Manager                  │
├─────────────────────────────────────────┤
│     PERSISTENCE (SQLite/PostgreSQL)     │
└─────────────────────────────────────────┘
```

### Ключевые компоненты

- **Command** — атомарная игровая операция
- **GameState** — in-memory состояние игры
- **PersistentGameState** — state с автосохранением в БД
- **CommandExecutor** — выполнитель команд с гарантиями
- **EventBus** — pub/sub система для реактивной логики
- **DataLoader** — загрузка контента из JSON
- **GameBot** — интеграция с Telegram (aiogram 3.x)

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| **[QUICKSTART.md](docs/QUICKSTART.md)** | Создание игры за 30 минут ⭐ |
| **[TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md)** | Полная техническая документация |
| **[API_REFERENCE.md](docs/API_REFERENCE.md)** | Справочник по API |
| **[templates/](templates/)** | Готовые шаблоны игр |
| **[CHANGELOG.md](CHANGELOG.md)** | История изменений |

---

## ✨ Новое в v0.6.0

**5 продвинутых игровых механик для CCG/Gacha игр:**

- 🎰 **Dynamic Banners** — временные баннеры гачи с автоматической ротацией
- ⚡ **Element Synergy** — синергия стихий для колод (бонусы за 3+ карты одного типа)
- 🔄 **Card Fusion** — слияние карт с Saga Pattern (атомарность гарантирована)
- 🐉 **World Raids** — глобальные боссы с миллиардами HP и optimistic locking
- 👥 **Referral System** — реферальное дерево с бонусами

📖 Подробнее: **[API_REFERENCE.md](docs/API_REFERENCE.md)** (раздел "Новые сервисы v0.6.0")

---

## 🎯 Для каких игр?

### ✅ Отлично подходит

- Turn-based RPG
- Idle/Clicker игры
- Roguelike/Roguelite
- Gacha/Collection игры
- Card Battle игры (CCG)
- Turn-based стратегии

### ❌ Не подходит

- Real-time игры (шутеры, гонки)
- Игры с физической симуляцией
- Графически-интенсивные игры

---

## 📊 Performance

| Метрика | Цель | Достигнуто |
|---------|------|------------|
| Выполнение команды | < 0.1ms | ✅ 0.007ms |
| Сохранение в БД | < 10ms | ✅ ~2ms |
| 1000 команд | < 100ms | ✅ 7.81ms |
| Concurrent operations | 0 race conditions | ✅ |
| Test coverage | > 85% | ✅ 89.76% |

---

## 📦 Установка

### Для использования движка

```bash
# Клонировать репозиторий
git clone https://github.com/yourusername/tg_bot_engine.git
cd tg_bot_engine

# Установить движок
pip install -e .

# С Telegram адаптером
pip install -e .[telegram]

# С dev зависимостями
pip install -e .[dev]
```

### Системные требования

- Python 3.9+
- SQLite 3+ (встроен в Python)
- 256MB+ RAM
- Linux/macOS/Windows

---

## 🧪 Тестирование

```bash
# Запустить все тесты
pytest

# С покрытием
pytest --cov=engine --cov-report=html

# Только бенчмарки
pytest -m benchmark

# Verbose режим
pytest -v
```

**Текущие результаты:** 196/196 тестов пройдено ✅ | Покрытие: 89.76% ✅

---

## 🗺️ Roadmap

- [x] **Iteration 0:** Proof of Concept ✅
- [x] **Iteration 1:** Транзакционность + Изоляция ✅
- [x] **Iteration 2:** Data-Driven System ✅
- [x] **Iteration 3:** Event System ✅
- [x] **Iteration 4:** Persistence Layer ✅
- [x] **Iteration 5:** Telegram Adapter ✅
- [x] **Iteration 5.5:** Engine Packaging ✅
- [x] **Iteration 5.6:** Templates & Refinement ✅
- [x] **Iteration 6.0:** Advanced Game Mechanics ✅
- [ ] **Iteration 7:** First Playable Game (в процессе)
- [ ] **Iteration 8:** Engine Extraction
- [ ] **Iteration 9:** Second Game Validation
- [ ] **Iteration 10:** Production Hardening

📖 История изменений: **[CHANGELOG.md](CHANGELOG.md)**

---

## 🤝 Поддержка

- **Issues:** [GitHub Issues](https://github.com/yourusername/tg_bot_engine/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/tg_bot_engine/discussions)
- **Telegram:** @tg_bot_engine_chat

---

## 📝 Лицензия

MIT License — см. [LICENSE](LICENSE)

---

## 🙏 Участие в разработке

Проект находится в активной разработке. После завершения Iteration 7 (First Playable Game) будет открыт для внешнего участия.

---

**Версия:** 0.6.0  
**Статус:** ✅ Stable — готов к созданию полноценных игр  
**Последнее обновление:** 2026-02-09
