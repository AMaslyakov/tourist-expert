# Правила и факты: workflow для `experta`

В проекте используется единая схема данных и ручные правила `experta`:

- `app/knowledge.py` хранит факты (`TRAVEL_FACTS`) для формы и входных данных движка.
- `app/forms.py` собирает `LandingForm` автоматически из `TRAVEL_FACTS`.
- `app/rules.py` хранит правила `@Rule` и API вывода (`evaluate`, `backward`).

## 1. Как добавить новый факт

Добавьте `FactSpec` в `TRAVEL_FACTS` в [knowledge.py](/home/avm/URFU/Практикум3/tourist-expert/app/knowledge.py).

Пример:

```python
FactSpec(
    name="season",
    label="Сезон",
    field_type="select",
    required=True,
    choices=(("winter", "Зима"), ("summer", "Лето")),
    validators=(ValidatorSpec(kind="required", message="Выберите сезон."),),
    fact_slot="season",
)
```

Что произойдет автоматически:

- поле появится в форме;
- значение попадет в `get_evaluation_input(...)`;
- факт станет доступен в `TravelInput(...)` для правил.

## 2. Как добавить новое правило

В [rules.py](/home/avm/URFU/Практикум3/tourist-expert/app/rules.py) добавьте метод с `@Rule` и метаданными `_register_rule(...)`.

```python
@_register_rule(
    name="winter-active",
    priority=260,
    recommendation="Рекомендуется активный зимний отдых.",
    conditions=(
        ConditionSpec(slot="season", op="eq", value="winter"),
        ConditionSpec(slot="travel_type", op="eq", value="active"),
        ConditionSpec(slot="budget_rub", op="gte", value=80000),
    ),
)
@Rule(
    TravelInput(season="winter", travel_type="active", budget_rub=MATCH.budget),
    TEST(lambda budget: budget >= 80000),
    salience=260,
)
def rule_winter_active(self, budget: int) -> None:
    self.register_match("winter-active")
```

`conditions` используются для explain и обратного вывода. Поддерживаемые операторы:

- `eq`
- `lt`, `lte`, `gt`, `gte`

## 3. Прямой и обратный вывод

Прямой вывод:

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

- `recommendation`
- `matched_rules`
- `selected_rule`
- `elapsed_ms`
- `passes`

Обратный вывод:

```python
backward = engine.backward(
    goal="warm-relax-premium",
    known_facts={
        "climate": "warm",
        "travel_type": "relax",
        "budget_rub": 120000,
    },
    explain=True,
)
```

`backward` содержит:

- `goal`, `achieved`
- `selected_rule`
- `steps` (детальная цепочка проверок)
- `elapsed_ms`, `passes`

## 4. Короткий чеклист

1. Добавили факт в `TRAVEL_FACTS` (если нужен новый вход).
2. Добавили `@Rule` + `_register_rule(...)` в `app/rules.py`.
3. Запустили `venv/bin/python -m unittest discover -s tests -v`.
4. Проверили форму и ответ через `venv/bin/python -m app`.
