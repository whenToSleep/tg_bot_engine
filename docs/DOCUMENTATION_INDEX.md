# 📚 Telegram Game Engine — Документация

**Версия:** 0.6.0  
**Дата:** 2026-02-09

---

## Навигация по документации

### 🚀 Для начинающих

1. **[README.md](../README.md)** — Начните отсюда!
   - Обзор проекта и возможностей
   - Быстрый старт с готовыми шаблонами
   - Простой пример использования
   - Roadmap и статус проекта

2. **[QUICKSTART.md](QUICKSTART.md)** — Создание игры за 30 минут
   - Два варианта: готовый шаблон или с нуля
   - Пошаговые инструкции
   - Примеры кода
   - Советы по отладке

### 📖 Для разработчиков

3. **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** — Полная техническая документация
   - Архитектура движка
   - Все основные компоненты
   - Системы движка (Transaction, Events, Data Loading)
   - Сервисы (Gacha, Matchmaking, Scheduler, Raid)
   - Продвинутые системы (Modifiers, Bonuses, Status)
   - Лучшие практики
   - **~12,000 слов** | **~40 минут чтения**

4. **[API_REFERENCE.md](API_REFERENCE.md)** — Справочник API
   - Полная документация всех классов и методов
   - Примеры кода для каждого компонента
   - Параметры и возвращаемые значения
   - **~15,000 слов** | **Справочник**

### 🎨 Дополнительные ресурсы

5. **Шаблоны игр** — Готовые примеры в папке `templates/`
   - `templates/rpg/` — Turn-based RPG
   - `templates/idle_clicker/` — Idle игра
   - `templates/card_game/` — Карточная игра
   - Каждый шаблон содержит README.md с инструкциями

6. **[CHANGELOG.md](../CHANGELOG.md)** — История изменений
   - Список всех изменений по версиям
   - Breaking changes
   - Миграция между версиями

---

## Быстрые ссылки по темам

### Основы

| Тема | Документ | Раздел |
|------|----------|--------|
| Что такое движок? | [README.md](../README.md) | О проекте |
| Установка | [QUICKSTART.md](QUICKSTART.md) | Шаг 1 |
| Первая игра | [QUICKSTART.md](QUICKSTART.md) | Шаги 2-7 |
| Архитектура | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) | Архитектура |

### Ядро движка

| Компонент | Документ | Раздел |
|-----------|----------|--------|
| Command | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Основные компоненты → Command |
| GameState | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Основные компоненты → GameState |
| CommandExecutor | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Основные компоненты → CommandExecutor |
| Events | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Системы движка → Event System |
| Data Loading | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Системы движка → Data Loading |

### Сервисы

| Сервис | Документ | Раздел |
|--------|----------|--------|
| GachaService | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Сервисы → Gacha Service |
| MatchmakingService | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Сервисы → Matchmaking Service |
| Scheduler | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Сервисы → Scheduler Service |
| BannerManager | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Сервисы → Banner Manager |
| RaidService | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Сервисы → Raid Service |

### Продвинутые темы

| Тема | Документ | Раздел |
|------|----------|--------|
| Stat Modifiers | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Продвинутые системы → Stat Modifiers |
| Bonus Calculator | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Продвинутые системы → Bonus Calculator |
| Entity Status | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md), [API_REFERENCE.md](API_REFERENCE.md) | Продвинутые системы → Entity Status |
| Unique Entities | TECHNICAL_DOCUMENTATION.md, API_REFERENCE.md | Продвинутые системы → Unique Entity |
| Card Fusion | [API_REFERENCE.md](API_REFERENCE.md) | Card Fusion (Saga Pattern) |
| Element Synergy | [API_REFERENCE.md](API_REFERENCE.md) | Element Synergy |

### Telegram Integration

| Тема | Документ | Раздел |
|------|----------|--------|
| GameBot | TECHNICAL_DOCUMENTATION.md, API_REFERENCE.md | Адаптеры → Telegram Adapter |
| ResponseBuilder | API_REFERENCE.md | Telegram Adapter → ResponseBuilder |
| MediaLibrary | TECHNICAL_DOCUMENTATION.md, API_REFERENCE.md | Продвинутые системы → Media Library |

---

## Рекомендуемый порядок изучения

### Уровень 1: Новичок (1-2 часа)
1. Прочитать **README.md** (10 минут)
2. Пройти **QUICKSTART.md** (30-60 минут)
3. Запустить готовый шаблон из папки `templates/` (10 минут)

### Уровень 2: Разработчик (3-5 часов)
1. Изучить **TECHNICAL_DOCUMENTATION.md** полностью (2-3 часа)
2. Просмотреть примеры в **API_REFERENCE.md** (1 час)
3. Изучить готовые шаблоны в `templates/` (1 час)

### Уровень 3: Эксперт (постоянно)
1. Использовать **API_REFERENCE.md** как справочник
2. Следить за **CHANGELOG.md** для обновлений
3. Изучать новые механики в разделе v0.6.0 документации

---

## Структура документов

### README.md
```
├── О проекте
├── Быстрый старт
├── Готовые шаблоны
├── Простой пример
├── Архитектура (краткая)
├── Документация (ссылки)
├── Новое в v0.6.0
├── Для каких игр
├── Performance
├── Установка
├── Тестирование
└── Roadmap
```

### QUICKSTART.md
```
├── Что мы создадим
├── Требования
├── Вариант 1: Готовый шаблон
├── Вариант 2: С нуля
│   ├── Шаг 1: Окружение
│   ├── Шаг 2: Структура
│   ├── Шаг 3: Схемы данных
│   ├── Шаг 4: Игровой контент
│   ├── Шаг 5: Конфигурация
│   ├── Шаг 6: Создание бота
│   ├── Шаг 7: Запуск
│   └── Шаг 8: Тестирование
├── Кастомизация
└── Следующие шаги
```

### TECHNICAL_DOCUMENTATION.md
```
├── Введение
├── Архитектура (подробная)
├── Основные компоненты
│   ├── Command
│   ├── GameState
│   ├── PersistentGameState
│   ├── CommandExecutor
│   └── CommandResult
├── Системы движка
│   ├── Transaction System
│   ├── Entity Locking
│   ├── Event System
│   └── Data Loading System
├── Сервисы
│   ├── Gacha Service
│   ├── Matchmaking Service
│   ├── Scheduler Service
│   ├── Banner Manager
│   └── Raid Service
├── Команды
├── События
├── Модули
├── Адаптеры
├── Хранение данных
├── Продвинутые системы
│   ├── Stat Modifiers
│   ├── Bonus Calculator
│   ├── Entity Status
│   ├── Unique Entity
│   ├── Utilities
│   └── Media Library
├── Производительность
└── Лучшие практики
```

### API_REFERENCE.md
```
├── Core (Command, GameState, Executor)
├── Persistence (Repository, SQLite)
├── Transactions
├── Data Loading
├── Events
├── Modules
├── Commands (Economy, Combat, Spawning, Gacha, Fusion)
├── Telegram Adapter
├── Utilities
├── Stat Modifiers System
├── Bonus Calculator System
├── Entity Status System
├── Unique Entity System
├── Gacha Service
├── Matchmaking Service
├── Media Library
├── Raid Service
└── Referral System
```

---

## Поиск информации

### Как найти нужную информацию?

**Вопрос:** "Как создать команду?"
→ **TECHNICAL_DOCUMENTATION.md** → Основные компоненты → Command
→ **API_REFERENCE.md** → Core → Command

**Вопрос:** "Как сделать gacha систему?"
→ **TECHNICAL_DOCUMENTATION.md** → Сервисы → Gacha Service
→ **API_REFERENCE.md** → Gacha Service

**Вопрос:** "Как добавить баффы/дебаффы?"
→ **TECHNICAL_DOCUMENTATION.md** → Продвинутые системы → Stat Modifiers
→ **API_REFERENCE.md** → Stat Modifiers System

**Вопрос:** "Как сделать временный баннер?"
→ **API_REFERENCE.md** → Scheduler + Dynamic Banners
→ **TECHNICAL_DOCUMENTATION.md** → Сервисы → Banner Manager

**Вопрос:** "Как начать разработку?"
→ **QUICKSTART.md** → Вариант 1 или 2

---

## Глоссарий

| Термин | Определение | Где искать |
|--------|-------------|------------|
| **Command** | Атомарная игровая операция | TECHNICAL_DOCUMENTATION.md |
| **Entity** | Игровая сущность (player, mob, item) | TECHNICAL_DOCUMENTATION.md |
| **State** | Состояние игры (все сущности) | TECHNICAL_DOCUMENTATION.md |
| **Executor** | Выполнитель команд | TECHNICAL_DOCUMENTATION.md |
| **Event** | Игровое событие (MobKilled, LevelUp) | TECHNICAL_DOCUMENTATION.md |
| **Module** | Реактивный игровой модуль | TECHNICAL_DOCUMENTATION.md |
| **Gacha** | Система случайных выпадений | API_REFERENCE.md |
| **Pity** | Гарантия в gacha системе | API_REFERENCE.md |
| **Modifier** | Модификатор стата (бафф/дебафф) | API_REFERENCE.md |
| **Saga** | Паттерн для сложных транзакций | API_REFERENCE.md |

---

## Часто задаваемые вопросы

### Общие

**Q: Какой документ читать первым?**
A: **README.md**, затем **QUICKSTART.md**

**Q: Где полная документация API?**
A: **API_REFERENCE.md** — справочник всех классов и методов

**Q: Где примеры кода?**
A: В **QUICKSTART.md**, **TECHNICAL_DOCUMENTATION.md** и **API_REFERENCE.md**

### Технические

**Q: Как предотвратить race conditions?**
A: Движок делает это автоматически через `get_entity_dependencies()`
→ **TECHNICAL_DOCUMENTATION.md** → Системы движка → Entity Locking

**Q: Как сделать транзакции с rollback?**
A: Используйте TransactionalExecutor или Saga Pattern
→ **TECHNICAL_DOCUMENTATION.md** → Системы движка → Transaction System

**Q: Как добавить персистентность?**
A: Используйте PersistentGameState вместо GameState
→ **TECHNICAL_DOCUMENTATION.md** → Основные компоненты → PersistentGameState

### Игровые механики

**Q: Как сделать систему гачи с pity?**
A: Используйте GachaService
→ **API_REFERENCE.md** → Gacha Service

**Q: Как сделать баффы и дебаффы?**
A: Используйте Stat Modifiers System
→ **API_REFERENCE.md** → Stat Modifiers System

**Q: Как сделать offline прогресс?**
A: Используйте calculate_offline_progress из utils
→ **API_REFERENCE.md** → Utilities → Idle/Clicker Utilities

---

## Обновления документации

**Последнее обновление:** 2026-02-09  
**Версия движка:** 0.6.0

### История изменений документации

**v0.6.0 (2026-02-09)**
- ✅ Добавлена документация по 5 новым механикам
- ✅ Добавлена документация по v0.6.0 в API_REFERENCE.md
- ✅ Обновлен CHANGELOG.md
- ✅ Расширен API_REFERENCE.md

**v0.5.6 (2025-XX-XX)**
- ✅ Добавлены готовые шаблоны в папку templates/
- ✅ Обновлен QUICKSTART.md

**v0.5.5 (2025-XX-XX)**
- ✅ Создан USAGE.md
- ✅ Создан API_REFERENCE.md
- ✅ Создан QUICKSTART_GAME.md

---

## Поддержка

Если вы не нашли ответ в документации:

1. **GitHub Issues:** Задайте вопрос или сообщите об ошибке
2. **GitHub Discussions:** Обсудите с сообществом
3. **Telegram:** @tg_bot_engine_chat

---

**Версия документации:** 0.6.0  
**Дата:** 2026-02-09  
**Статус:** ✅ Актуальная
