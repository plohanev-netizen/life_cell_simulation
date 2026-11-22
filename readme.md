# Cell Wars — Cellular Simulation

Интерактивная симуляция клеточного автомата на Python (`pygame + numpy`) с постепенным усложнением логики: фракции, антистагнационные взрывы, рейдеры и вирусы.

Interactive cellular automaton simulation written in Python (`pygame + numpy`) with gradually increasing complexity: factions, anti-stagnation explosions, raiders and viruses.

Проект развивался **последовательно**, каждая значимая стадия сохранена в репозитории отдельным файлом.

The project evolved **step by step**, each major development stage is preserved in the repository as a separate file.

---

## Веб-версия

Откройте [docs/index.html](docs/index.html) в браузере. Для запуска по HTTP
выполните в корне репозитория `python3 -m http.server 8000 --bind 127.0.0.1 --directory docs`
и откройте `http://127.0.0.1:8000/`. Дополнительные библиотеки не нужны.

В интерфейсе можно выбрать русский или английский язык.

В браузере доступны две фракции, стагнация и автоматическое перезаселение,
рейдеры, вирусные волны, ручные бомбы и счётчики. Для ручного взрыва
выберите инструмент «Бомба» и нажмите на поле. Если очистить поле и
запустить симуляцию с включёнными мутациями, через 30 поколений
автоматический взрыв снова заселит поле.

Осцилляторы с периодом от 2 до 4 поколений взрываются после 100 полных
повторений. Радиус такого взрыва в 1,5 раза больше радиуса ручной бомбы
с округлением до целой клетки. «Вирусная бомба» заполняет область
вирусами и включает вирусный режим, если он был выключен.


Браузерная версия адаптирована из `life_and_viruses.py`. Размер поля,
радиусы и параметры рейдеров масштабированы для веб-версии.
Вирусы появляются отдельными волнами, графики и журналы Python не перенесены.
На сенсорных устройствах симуляция запускается сама. Тап по полю
сбрасывает обычную бомбу. Панель настроек доступна в режиме с мышью.

Для GitHub Pages выберите ветку с веб-версией и папку `/docs`.

---

## 📁 Файлы в репозитории / Repository Files

### 1️⃣ `main.py`
**Первая стабильная версия симуляции**  
**First stable version of the simulation**

- Классическая игра «Жизнь» (Game of Life)
- Конечное поле (без wrap-around)
- Базовые правила рождения и смерти клеток
- Визуализация через `pygame`

- Classic Game of Life
- Finite grid (no wrap-around)
- Basic birth and death rules
- Visualization using `pygame`

---

### 2️⃣ `two_thrones.py`
**Версия с фракциями**  
**Version with factions**

- Добавлены две враждующие фракции:
  - 🔴 красные
  - ⚪ белые
- Фракции стартуют с разных сторон поля
- Рождение клеток с учётом цвета соседей
- Начало конфликтной динамики

- Two opposing factions introduced:
  - 🔴 red
  - ⚪ white
- Factions start on opposite sides of the field
- Cell birth depends on neighbor colors
- Emergent conflict dynamics

---

### 3️⃣ `stagnation_boom.py`
**Антистагнация и райдеры**  
**Anti-stagnation and raiders**

- Введено понятие *активности поля*
- При стагнации автоматически происходят **взрывы**:
  - один большой
  - или несколько малых
- Реализованы **райдеры**:
  - малые изолированные группы клеток
  - при контакте с врагом совершают взрыв
  - очищают область и заселяют её своим цветом
- Добавлен debug-режим для райдеров

- Field *activity* metric introduced
- Automatic **explosions** on stagnation:
  - one large
  - or multiple small
- **Raiders** implemented:
  - small isolated cell groups
  - explode upon enemy contact
  - clear the area and recolonize it with their own color
- Raider debug mode added

---

### 4️⃣ `life_and_viruses.py`
**Биологическая угроза — вирусы**  
**Biological threat — viruses**

- Добавлен новый тип клеток: 🦠 **вирус**
- Вирус — не фракция, а заражающий фактор
- Может появляться:
  - спонтанно, случайными группами
  - при взрывах (BIG_BANG / RAIDERS)
- Заражает любые соседние клетки
- Имеет ограниченный жизненный цикл и механику очистки

- New cell type added: 🦠 **virus**
- Virus is not a faction but an infecting factor
- Can appear:
  - spontaneously, in random groups
  - during explosions (BIG_BANG / RAIDERS)
- Infects any neighboring cells
- Has a limited lifetime and cleanup mechanics

---

## 🎮 Управление / Controls

### ⌨️ Клавиатура / Keyboard

- `Space` — пауза / запуск симуляции  
  Pause / resume simulation
- `R` — reset (перезапуск)  
  Reset simulation
- `C` — очистка поля  
  Clear the field
- `F` — полноэкранный режим  
  Toggle fullscreen
- `UP / DOWN` — скорость симуляции  
  Decrease / increase simulation speed
- `H` — справка (overlay)  
  Toggle help overlay
- `E` — райдеры ON / OFF  
  Raiders ON / OFF
- `Y` — отладка райдеров  
  Raider debug mode
- `V` — Biohazard (вирусы ON / OFF)

---

### 🖱️ Мышь / Mouse

- **ЛКМ / LMB** — поставить группу из 4 белых клеток  
  Place a group of 4 white cells
- **ПКМ / RMB** — поставить группу из 4 красных клеток  
  Place a group of 4 red cells
- **Shift + ЛКМ** — ластик (удаление клеток)  
  Erase cells
- **Удержание ЛКМ ~0.5 сек** — ручной мини-взрыв  
  Hold LMB ~0.5s — manual mini-explosion

---

## 🧪 Примечания / Notes

- Проект экспериментальный и исследовательский
- Архитектура намеренно монолитная для быстрого прототипирования
- Логика усложняется от файла к файлу — рекомендуется изучать версии **по порядку**

- Experimental, research-oriented project
- Architecture is intentionally monolithic for rapid prototyping
- Logic complexity increases with each file — recommended to explore versions **in order**

---

## 🔮 Дальнейшие идеи / Future ideas

- Санитары (антивирусные юниты)
- Дополнительные режимы вирусов
- Рефакторинг и перенос логики в веб-приложение

- Sanitizers (anti-virus units)
- Additional virus behavior modes
- Refactoring and migration to a web-based application

---

**Cell Wars** — эксперимент с эмерджентным поведением, конфликтами и устойчивостью сложных систем.

**Cell Wars** is an experiment in emergent behavior, conflict, and resilience of complex systems.
