# Как работает приоритет правил в `app` (модуль `experta`)

В проекте приоритет задается вручную для каждого правила и используется в двух местах одновременно:

1. В метаданных правила (`RuleMetadata.priority`) через декоратор `_register_rule(...)`.
2. В механизме конфликтов `experta` через `salience` (в `_register_rule` приоритет копируется в `rule_callable.salience`).

## Механика выбора правила

1. Правила, условия которых выполнены, попадают в список совпавших (`matched_rules`).
2. При каждом совпадении вызывается `register_match(rule_name)`.
3. `register_match` сравнивает `metadata.priority` с текущим `selected_priority`.
4. Выбирается правило с **максимальным** приоритетом.
5. Если ничего не совпало, срабатывает `default-recommendation` с приоритетом `-1000`.

Итог: приоритет не вычисляется автоматически от числа условий; он задается разработчиком и определяет победителя при конкуренции правил.

## Примеры из `app/rules.py`

Ниже примеры проверены на текущем движке `TravelRuleEngine` (`evaluate(..., explain=True)`).

1. **Премиальный спокойный отдых в теплом климате**
   Входные факты:  
   `season=summer, hobby=museum, budget_rub=150000, trip_days=10, climate=warm, travel_type=relax, companions=couple, service_level=premium, visa_mode=visa_ready, insurance=yes`
   
   Совпали правила:
   - `warm-relax-premium` (340)
   - `premium-visa-ready-relax` (323)
   - `couple-relax-premium` (286)
   - `warm-summer-beach` (283)
   - `service-premium-comfort` (275)
   - `hobby-museum-city` (270)
   - `relax-general` (245)
   
   Выбрано: **`warm-relax-premium`**, потому что `340` — максимальный приоритет.

2. **Короткая деловая поездка без визы**
   Входные факты:  
   `season=summer, hobby=museum, budget_rub=70000, trip_days=4, climate=warm, travel_type=business, companions=solo, service_level=standard, visa_mode=visa_free_only, insurance=yes`
   
   Совпали правила:
   - `business-short-standard` (291)
   - `warm-summer-beach` (283)
   - `visa-free-short-trip` (278)
   - `visa-free-business-quick` (277)
   - `hobby-museum-city` (270)
   - `business-general` (250)
   
   Выбрано: **`business-short-standard`**, потому что `291` выше остальных.

3. **Недостаточно фактов (fallback)**
   Входные факты: `{}` (пустой набор).
   
   Совпали правила:
   - `default-recommendation` (-1000)
   
   Выбрано: **`default-recommendation`**, так как специализированные правила не могут быть доказаны без входных фактов.

