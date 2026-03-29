# Правила и факты: простой workflow

Теперь в проекте есть единая точка входа:

- `app/knowledge.py` хранит **факты** (`TRAVEL_FACTS`) и **правила** (`TRAVEL_RULES`).
- Форма и движок автоматически используют эти структуры.

## 1. Как добавить новый факт

Добавляете только запись в `TRAVEL_FACTS` в [knowledge.py](/home/avm/URFU/Практикум3/tourist-expert/app/knowledge.py).

Пример:

```python
FactSpec(
    name="season",
    label="Сезон",
    field_type="select",
    required=True,
    choices=(
        ("winter", "Зима"),
        ("summer", "Лето"),
    ),
    validators=(ValidatorSpec(kind="required", message="Выберите сезон."),),
    fact_slot="season",
    clip_type="SYMBOL",
)
```

Что произойдет автоматически:

- поле появится в форме;
- факт попадет в `evaluate(...)`;
- слот добавится в `travel-input` шаблон CLIPS.

## 2. Как добавить новое правило

Добавляете только запись в `TRAVEL_RULES` в [knowledge.py](/home/avm/URFU/Практикум3/tourist-expert/app/knowledge.py).

Пример:

```python
RuleSpec(
    name="winter-active",
    priority=260,
    when=(
        ConditionSpec(slot="season", op="eq", value="winter"),
        ConditionSpec(slot="travel_type", op="eq", value="active"),
        ConditionSpec(slot="budget_rub", op="gte", value=80000),
    ),
    recommendation="Рекомендуется активный зимний отдых.",
)
```

Поддерживаемые операторы:

- `eq` — равно
- `lt`, `lte`, `gt`, `gte` — числовые сравнения

`default`-ветка уже есть и срабатывает, если ни одно правило не подошло.

## 3. Как понять, что правило реально сработало

Движок поддерживает explain-режим:

```python
result = engine.evaluate(
    {
        "hobby": "dance",
        "budget_rub": 120000,
        "trip_days": 8,
        "climate": "warm",
        "travel_type": "relax",
        "companions": "couple",
    },
    explain=True,
)
```

`result` содержит:

- `recommendation` — итоговая рекомендация;
- `matched_rules` — список всех подошедших правил;
- `selected_rule` — правило-победитель по приоритету;
- `elapsed_ms` — время вывода.

## 4. Короткий чеклист

1. Добавили факт в `TRAVEL_FACTS` (если нужен новый вход).
2. Добавили правило в `TRAVEL_RULES`.
3. Запустили `venv/bin/python -m unittest discover -s tests -v`.
4. Проверили форму и ответ в браузере через `venv/bin/python -m app`.
