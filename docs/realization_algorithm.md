# Реализация продукционной системы и алгоритм работы

## 1. Назначение и контекст

Прототип реализует консультационную экспертную систему по туризму на базе:

- `Flask` (веб-интерфейс и маршрутизация),
- `WTForms/Flask-WTF` (валидация и сбор входных данных),
- `experta` (прямой вывод правил на основе RETE),
- собственный слой обратного вывода (в `app/rules.py`).

Ключевая особенность реализации:  
**форма и факты schema-driven**, а правила описаны вручную и сопровождаются explain-метаданными.

## 2. Структура реализации в проекте

1. `app/knowledge.py`  
   Описывает факты (`TRAVEL_FACTS`) и модель условий (`ConditionSpec`).

2. `app/form_factory.py` + `app/forms.py`  
   Генерируют `LandingForm` из `TRAVEL_FACTS` и формируют два payload:
   - для вывода (`get_evaluation_input`) по `fact_slot`,
   - для хранения сессии (`get_session_input`).

3. `app/rules.py`  
   Содержит:
   - `experta`-движок `_TravelExpertEngine` (forward chaining),
   - фасад `TravelRuleEngine` (`evaluate`, `backward`),
   - explain-результаты `EvaluationResult`, `BackwardResult`,
   - метаданные приоритетов и условий (`RuleMetadata`).

4. `app/__init__.py`  
   Связывает форму и движок в маршруте `/`:
   `validate -> evaluate -> backward -> save session -> render result`.

5. `app/session_store.py`  
   Сохраняет консультации как JSON (`consultation/*.json`).

6. `app/experta_compat.py`  
   Патчит `collections.*` alias для совместимости `experta` с Python 3.14.

## 3. Алгоритм работы приложения (end-to-end)

### 3.1 Основной сценарий маршрута `/`

1. Пользователь открывает `GET /` -> рендерится форма `LandingForm`.
2. Пользователь отправляет `POST /`.
3. Выполняется `form.validate_on_submit()`.
4. Если форма невалидна -> повторный рендер формы с ошибками.
5. Если форма валидна:
   - собираются факты для движка (`evaluation_input`);
   - выполняется прямой вывод `evaluate(..., explain=True)`;
   - выполняется обратный вывод `backward(goal="*", ..., explain=True)`;
   - сохраняется JSON-сессия (`input`, `recommendation`, `explain.forward`, `explain.backward`);
   - рендерится карточка рекомендации.

### 3.2 Псевдокод боевого цикла

```text
form = LandingForm()
if form.validate_on_submit():
    facts = get_evaluation_input(form)
    fwd = engine.evaluate(facts, explain=True)
    bwd = engine.backward(goal="*", known_facts=facts, explain=True)
    save_consultation_session({input, recommendation=fwd.recommendation, explain={fwd,bwd}})
    show_recommendation_card(fwd.recommendation)
else:
    show_form_with_errors()
```

## 4. Алгоритм прямого вывода (forward chaining)

Реализован через `experta` (`KnowledgeEngine` + `@Rule`).

### 4.1 Вход

Словарь фактов пользователя после нормализации:

- целочисленные поля приводятся к `int`,
- пустые/`None` значения исключаются.

### 4.2 Шаги `evaluate(...)`

1. `reset_runtime_state()` в `_TravelExpertEngine`.
2. `engine.reset()` (сброс agenda/fact-list/matcher).
3. `engine.declare(TravelInput(**normalized))`.
4. `engine.run()`:
   - matcher строит/обновляет activations,
   - strategy сортирует agenda,
   - берется следующая activation,
   - вызывается RHS-метод правила.
5. При срабатывании правила вызывается `register_match(rule_name)`:
   - правило добавляется в `matched_rules`,
   - если его `priority` выше текущего, оно становится `selected_rule`.
6. Возвращается рекомендация и explain-структура (`steps`, `matched_rules`, `selected_rule`, `elapsed_ms`).

### 4.3 Разрешение конфликтов

Приоритет задается вручную в `_register_rule(..., priority=...)` и синхронизируется с `Rule(..., salience=...)`.  
Побеждает правило с максимальным приоритетом; если совпадений нет — `default-recommendation`.

## 5. Алгоритм обратного вывода (custom backward chaining)

Важно: в данном проекте обратный вывод реализован **собственным алгоритмом** в `TravelRuleEngine.backward(...)`, а не встроенным механизмом `experta`.

### 5.1 Идея

- Цель `goal="*"`: найти лучшее доказуемое правило среди всех кандидатов.
- Цель `goal="<rule-name>"`: доказать конкретное правило.

### 5.2 Шаги

1. Нормализация `known_facts`.
2. Выбор списка кандидатов:
   - `*` -> все правила по убыванию `priority`,
   - конкретная цель -> одно правило либо `goal-not-found`.
3. Для каждого кандидата:
   - проверка каждого условия (`slot`, `op`, `value`),
   - фиксация шагов (`prove-condition`, `condition-from-facts`/`condition-failed`),
   - итог `rule-proved` или `rule-failed`.
4. Первый доказанный кандидат становится `selected_rule`.
5. Если кандидат не найден и цель общая (`*`) -> fallback на `default-recommendation`.
6. Формируется `BackwardResult` с полем `proof` и детальной трассировкой `steps`.

### 5.3 Псевдокод

```text
candidates = sorted_rules_by_priority(goal)
for candidate in candidates:
    ok = all(condition_is_true(cond, known_facts) for cond in candidate.conditions)
    if ok and selected is None:
        selected = candidate
if selected is None and goal in {"*", default}:
    selected = default_rule
return BackwardResult(selected, steps, proof)
```

## 6. Внутреннее устройство `experta` (по документации и исходникам)

Ниже — практическая модель компонентов `experta`, на которых построен ваш forward-вывод.

### 6.1 `KnowledgeEngine` (ядро)

`KnowledgeEngine` хранит:

1. `facts` (`FactList`),
2. `agenda` (`Agenda`),
3. `matcher` (`ReteMatcher`),
4. `strategy` (`DepthStrategy` по умолчанию).

Базовый цикл: `reset()` -> `declare()` -> `run()`.

### 6.2 `FactList` (рабочая память)

- хранит факты с `__factid__`,
- поддерживает `declare`/`retract`,
- отслеживает изменения (`added`, `removed`),
- предотвращает дубли (если `duplication=False`).

### 6.3 Matcher: `ReteMatcher`

`ReteMatcher` строит сеть RETE в два этапа:

1. **alpha-part**:
   - выделение проверок фактов (`TypeCheck`, `FeatureCheck`, `FactCapture`),
   - построение `FeatureTesterNode` от `BusNode`.
2. **beta-part**:
   - wiring условий правила через `OrdinaryMatchNode`/`NotNode`/`WhereNode`,
   - добавление `ConflictSetNode` как терминального узла правила.

### 6.4 Token-ориентированная обработка

При добавлении/удалении фактов `BusNode` создаёт токены:

- `Token.valid(...)`,
- `Token.invalid(...)`.

Токены проходят по сети, формируя/снимая activations в `ConflictSetNode`.

### 6.5 Activation, Agenda, Strategy

1. `ConflictSetNode` создаёт объекты `Activation(rule, facts, context)`.
2. `Strategy.update_agenda(...)` добавляет/удаляет activation в agenda.
3. `DepthStrategy` ранжирует activations по ключу:
   - `salience`,
   - id фактов (в обратном порядке).
4. `Agenda.get_next()` возвращает следующее правило к выполнению.

### 6.6 Выполнение RHS правила

`KnowledgeEngine.run()` извлекает activation из agenda и вызывает RHS-функцию правила, передавая контекст сопоставления (bind-переменные).

## 7. Как это связано с вашим проектом

1. Ваш `_TravelExpertEngine` наследует `KnowledgeEngine` и использует стандартный `ReteMatcher`.
2. Каждое правило оформлено как:
   - метаданные (`_register_rule`): `name`, `priority`, `recommendation`, `conditions`,
   - `experta`-правило (`@Rule(...)`) для forward-вывода.
3. Forward-часть делегирована `experta`, backward-часть реализована вручную для explain-режима и учебной трассировки.
4. На уровне Flask маршрут `/` объединяет оба вывода в один пользовательский результат и сохраняет объяснение в JSON.

## 8. Источники (web + первичные материалы)

1. Experta Documentation — The Basics:  
   https://experta.readthedocs.io/en/latest/thebasics.html
2. Experta Documentation — Reference (Facts/Rules/Agenda/Salience и CE):  
   https://experta.readthedocs.io/en/latest/reference.html
3. Experta API index:  
   https://experta.readthedocs.io/en/latest/api.html
4. RETE algorithm paper (оригинальная ссылка из модуля `experta.matchers.rete`):  
   http://reports-archive.adm.cs.cmu.edu/anon/scan/CMU-CS-79-forgy.pdf

Дополнительно для точной привязки к реализации использованы исходники установленного пакета:
`venv/lib/python3.14/site-packages/experta/*`.

