# Архитектура прототипа экспертной системы

## 1. Общая идея

Прототип реализован как монолитное Flask-приложение с продукционным движком на `experta`.

Система решает задачу консультации по путешествиям в одном цикле:

1. пользователь заполняет форму;
2. данные преобразуются в факты;
3. выполняется прямой вывод и выбирается рекомендация;
4. выполняется обратный вывод для объяснения;
5. результат и explain-данные сохраняются в JSON;
6. рекомендация показывается на той же странице.

## 2. Компоненты `app`

1. `app/__main__.py`  
   Точка локального запуска (`python -m app`), поднимает Flask на `127.0.0.1:5000`.

2. `app/__init__.py`  
   Фабрика приложения `create_app()`, настройка `SECRET_KEY`, CSRF, инициализация движка, регистрация маршрутов:
   `GET/POST /` и `GET /test`.

3. `app/knowledge.py`  
   Единый реестр знаний и схемы:
   `FactSpec`, `ValidatorSpec`, `ConditionSpec`, `TRAVEL_FACTS`, `DEFAULT_RECOMMENDATION`.

4. `app/form_factory.py`  
   Schema-driven сборка WTForms-класса и payload-ов:
   `build_form_class`, `build_fact_payload`, `build_session_payload`.

5. `app/forms.py`  
   Публичный слой форм:
   `LandingForm`, `VISIBLE_FORM_FIELDS`, `SUBMIT_FIELD_NAME`,
   адаптеры `get_evaluation_input()` и `get_session_input()`.

6. `app/rules.py`  
   Ядро экспертной системы:
   декларация правил `@Rule(...)`, метаданные приоритета, прямой/обратный вывод,
   explain-структуры `EvaluationResult` и `BackwardResult`.

7. `app/experta_compat.py`  
   Compatibility-слой для современных Python: патчит устаревшие alias в `collections`,
   которые используются зависимостями `experta`.

8. `app/session_store.py`  
   Файловое хранилище сессий: создаёт директорию `consultation/` и сохраняет JSON
   с уникальным именем и UTC-временем.

9. `app/templates/index.html` и `app/templates/test.html`  
   Шаблоны UI:
   главная форма/результат и отладочная страница для демонстрации цепочек вывода.

10. `app/static/images/recommendation-cover.svg`  
    Статический ресурс карточки рекомендации.

## 3. Логическая схема взаимодействия

```text
TRAVEL_FACTS (knowledge.py)
    -> form_factory.py строит LandingForm
    -> пользовательский ввод (/)
    -> get_evaluation_input() -> facts для движка
    -> TravelRuleEngine.evaluate(explain=True) [forward]
    -> TravelRuleEngine.backward(goal="*", explain=True) [backward]
    -> save_consultation_session() -> consultation/*.json
    -> index.html показывает рекомендацию
```

## 4. Потоки выполнения

### 4.1 Главный маршрут `/` (боевой сценарий)

1. Создается `LandingForm`.
2. `validate_on_submit()` валидирует поля и CSRF.
3. Из формы строится словарь фактов (`fact_slot`-поля из `TRAVEL_FACTS`).
4. Выполняется `evaluate(..., explain=True)`:
   фиксируются совпавшие правила, выбранное правило, шаги, время.
5. Выполняется `backward(goal="*", ..., explain=True)`:
   строится доказательство цели, шаги подцелей и кандидатов.
6. Собирается payload с секциями:
   `input`, `recommendation`, `explain.forward`, `explain.backward`.
7. Payload сохраняется в JSON через `session_store`.
8. Пользователь получает карточку с итоговой рекомендацией.

### 4.2 Сервисный маршрут `/test`

1. Без параметра `run_tests=1` показывает экран ожидания.
2. С `run_tests=1` запускает forward + backward на встроенном наборе фактов.
3. Отображает:
   выбранные правила, цепочку шагов обратного вывода, candidate chains,
   список всех правил с приоритетом.

## 5. Ядро вывода и explain

### 5.1 Прямой вывод

`TravelRuleEngine.evaluate()` нормализует факты, объявляет `TravelInput` в `experta`,
запускает `engine.run()` и возвращает либо строку рекомендации, либо `EvaluationResult`.

Структура explain forward:

1. `matched_rules`;
2. `selected_rule`;
3. `elapsed_ms`;
4. `passes`;
5. `steps` (декларация фактов, проверка условий, выбор правила/fallback).

### 5.2 Обратный вывод

`TravelRuleEngine.backward()` доказывает цель:

1. выбирает кандидатов (`goal="*"` -> все правила по приоритету);
2. по каждому кандидату доказывает условия;
3. фиксирует шаги (`prove-goal`, `try-rule`, `prove-condition`, `rule-proved` и т.д.);
4. при отсутствии совпадений для общей цели применяет `default-recommendation`.

Структура explain backward:

1. `goal`;
2. `achieved`;
3. `selected_rule`;
4. `matched_rules`;
5. `elapsed_ms`;
6. `passes`;
7. `steps`;
8. `proof` (дерево кандидатов и условий).

## 6. Приоритеты и разрешение конфликтов

Каждое правило получает `priority` в `_register_rule(...)`.
Этот же приоритет переносится в `salience` для `experta`.

При нескольких совпавших правилах побеждает правило с максимальным `priority`.
Если ничего не совпало, включается `default-recommendation` с приоритетом `-1000`.

На текущий момент в базе:

1. 55 пользовательских правил;
2. 1 правило fallback (`default-recommendation`).

## 7. Хранение данных и границы системы

1. База данных не используется.
2. История консультаций хранится в файловой системе (`consultation/*.json`).
3. Прототип без ролей и авторизации.
4. UI, логика форм, вывод и сохранение находятся в одном приложении Flask.

## 8. Расширяемость

Архитектура ориентирована на расширение через схему знаний:

1. новый факт добавляется в `TRAVEL_FACTS`;
2. форма и payload собираются автоматически;
3. правило добавляется в `app/rules.py` как `@Rule` + `_register_rule` метаданные;
4. explain и `/test` автоматически используют новые метаданные правил.

