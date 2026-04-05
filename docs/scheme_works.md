# Схема работы приложения `app` (для построения диаграммы)

Документ описывает основной пользовательский сценарий маршрута `/`:  
**вход через форму -> вывод правил -> сохранение сессии -> карточка рекомендации**.

## 1. Основные сущности

1. Пользователь (браузер).
2. Flask-приложение (`create_app`, маршрут `/`).
3. Форма `LandingForm` (генерируется из `TRAVEL_FACTS`).
4. Движок правил `TravelRuleEngine` (`evaluate` + `backward`).
5. Файловое хранилище сессий (`consultation/*.json`).
6. Шаблон `index.html` (режим формы / режим карточки рекомендации).

## 2. Какие формы используются и как переключаются

Используется одна пользовательская форма: **`LandingForm`**.

Форма собирается динамически из `app/knowledge.py` (`TRAVEL_FACTS`) через:

- `build_form_class(...)` в `app/form_factory.py`;
- экспорт в `app/forms.py` как `LandingForm`.

Визуально в `index.html` есть два состояния:

1. `recommendation_text == None` -> показывается форма (`<form method="post">`).
2. `recommendation_text != None` -> показывается карточка рекомендации и кнопка  
   «Новая консультация» (`GET /`), которая возвращает к форме.

## 3. Узлы для диаграммы (блоки)

1. **Start / GET `/`**
2. **Создание `LandingForm`**
3. **Рендер формы (`index.html`, режим form-panel)**
4. **POST `/` (submit формы)**
5. **Проверка `form.validate_on_submit()`**
6. **Ошибка валидации** -> возврат к форме с `field.errors`
7. **Сбор фактов для вывода** (`get_evaluation_input(form)`)
8. **Прямой вывод** (`engine.evaluate(..., explain=True)`)
9. **Обратный вывод** (`engine.backward(goal="*", ..., explain=True)`)
10. **Сбор payload с explain-данными**
11. **Сохранение JSON** (`save_consultation_session`)
12. **Рендер карточки рекомендации (`index.html`, режим result-layout)**
13. **Кнопка «Новая консультация» -> GET `/`**
14. **End**

## 4. Переходы между узлами (стрелки + условия)

1. `Start GET / -> Создание LandingForm`
2. `Создание LandingForm -> Рендер формы`
3. `Рендер формы -> POST /` (пользователь нажал submit)
4. `POST / -> Проверка validate_on_submit`
5. `validate_on_submit == False -> Ошибка валидации -> Рендер формы`
6. `validate_on_submit == True -> Сбор фактов`
7. `Сбор фактов -> Прямой вывод`
8. `Прямой вывод -> Обратный вывод`
9. `Обратный вывод -> Сбор payload`
10. `Сбор payload -> Сохранение JSON`
11. `Сохранение JSON -> Рендер карточки рекомендации`
12. `Карточка рекомендации -> Кнопка "Новая консультация" -> GET / -> Рендер формы`

## 5. Детализация блока «Прямой вывод»

Вход: словарь фактов из формы (`fact_slot`-поля).

Шаги:

1. Нормализация типов (`_normalize_facts`): числа -> `int`, пустые значения пропускаются.
2. Сброс runtime-состояния движка.
3. `declare(TravelInput(**facts))`.
4. `engine.run()` (механизм `experta`).
5. Сбор explain результата:
   - `matched_rules`;
   - `selected_rule`;
   - `recommendation`;
   - `elapsed_ms`;
   - `steps` (declare-facts, check-condition, rule-matched, select-rule/fallback-default).

Выход: `EvaluationResult` и текст рекомендации.

## 6. Детализация блока «Обратный вывод»

Цель в основном сценарии: `goal="*"` (найти лучшее доказуемое правило).

Шаги:

1. Нормализация известных фактов.
2. Выбор кандидатов правил по приоритету (убывание).
3. По каждому кандидату:
   - `try-rule`;
   - доказательство каждой подцели `prove-condition`;
   - фиксация `rule-proved` или `rule-failed`.
4. Выбор первого успешного кандидата как `selected_rule`.
5. Если ничего не доказано -> `fallback-default`.
6. Сбор explain результата:
   - `goal`, `achieved`, `selected_rule`;
   - `matched_rules`;
   - `steps`;
   - `proof` (дерево кандидатов и условий);
   - `elapsed_ms`, `passes`.

Выход: `BackwardResult` для объяснения и трассировки решения.

## 7. Что попадает в сохраненную сессию

В `consultation/consultation_<timestamp>_<id>.json` сохраняется:

1. `created_at_utc`;
2. `input` (данные формы через `get_session_input`);
3. `recommendation`;
4. `explain.forward`:
   `matched_rules`, `selected_rule`, `elapsed_ms`, `passes`, `steps`;
5. `explain.backward`:
   `goal`, `achieved`, `selected_rule`, `matched_rules`,
   `recommendation`, `elapsed_ms`, `passes`, `steps`, `proof`.

## 8. Финальное состояние UI (вывод)

После успешного POST и вывода правил пользователь видит:

1. карточку рекомендации (`recommendation-card`);
2. изображение (`static/images/recommendation-cover.svg`);
3. заголовок «Рекомендация системы»;
4. текст итоговой рекомендации;
5. кнопку «Новая консультация» для возврата к форме.

---

Эти блоки и переходы можно напрямую переносить в activity diagram или sequence diagram.

