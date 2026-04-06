# Продукционные правила экспертной системы

Документ описывает фактическую реализацию базы правил из `app/rules.py`.
В текущей версии движок содержит:

- `67` явных продукционных правил;
- `1` fallback-правило `default-recommendation`;
- прямой вывод через `TravelRuleEngine.evaluate(...)`;
- обратный вывод через `TravelRuleEngine.backward(...)`.

## Формат правила

Каждое правило в коде задается парой:

- `@_register_rule(...)` - метаданные для explain-режима;
- `@Rule(...)` - условие срабатывания в `experta`.

Метаданные правила содержат:

- `name` - стабильный идентификатор;
- `priority` - приоритет выбора;
- `recommendation` - итоговая рекомендация;
- `conditions` - список условий в виде `ConditionSpec(slot, op, value)`.

Если одновременно совпало несколько правил, движок выбирает правило с максимальным `priority`.

## Используемые факты

В логическом выводе участвуют следующие слоты:

- `season`
- `hobby`
- `budget_rub`
- `trip_days`
- `climate`
- `travel_type`
- `companions`
- `service_level`
- `visa_mode`
- `insurance`

Поле `notes` в правилах не участвует.

Поддерживаемые операторы условий:

- `eq`
- `lt`
- `lte`
- `gt`
- `gte`

## Прямой вывод

`TravelRuleEngine.evaluate(...)` работает так:

1. Нормализует входные факты.
2. Объявляет один факт `TravelInput(**normalized)`.
3. Запускает `experta`.
4. Сохраняет все сработавшие правила в `matched_rules`.
5. Выбирает правило с наибольшим приоритетом как `selected_rule`.
6. Если правил не найдено, применяет `default-recommendation`.

В explain-режиме возвращается `EvaluationResult` со структурой:

- `recommendation`
- `matched_rules`
- `selected_rule`
- `elapsed_ms`
- `passes=3`
- `steps`

## Обратный вывод

`TravelRuleEngine.backward(...)` реализован вручную поверх метаданных правил.

Особенности:

- `goal="*"` означает: проверить все правила по убыванию приоритета и найти лучшее доказуемое;
- для каждого кандидата проверяются все его `conditions`;
- если цель неизвестна, возвращается `goal-not-found`;
- если ни одно правило не доказано и цель равна `*` или `default-recommendation`, выбирается fallback.

В explain-режиме возвращается `BackwardResult`:

- `goal`
- `achieved`
- `selected_rule`
- `matched_rules`
- `recommendation`
- `elapsed_ms`
- `passes`
- `steps`
- `proof`

## Каталог правил

Ниже перечислены правила в том же приоритетном порядке, в котором они рассматриваются при объяснении.

### Приоритеты 340-323

1. `warm-relax-premium` (`340`): если `climate=warm`, `travel_type=relax`, `budget_rub>=100000`, то рекомендуется пляжный отдых в теплой стране повышенного комфорта.
2. `summer-family-beach` (`338`): если `season=summer`, `climate=warm`, `companions=family`, то рекомендуется семейный летний пляжный отдых.
3. `winter-active-ski` (`337`): если `season=winter`, `climate=cold`, `travel_type=active`, то рекомендуется зимний активный тур с горнолыжным курортом.
4. `family-health-insured` (`336`): если `companions=family`, `travel_type=health`, `insurance=yes`, то рекомендуется семейная оздоровительная программа.
5. `business-premium-city` (`335`): если `travel_type=business`, `service_level=premium`, `budget_rub>=90000`, то рекомендуется деловая поездка в крупный город с премиальным сервисом.
6. `visa-free-family-sea` (`334`): если `visa_mode=visa_free_only`, `companions=family`, `climate=warm`, то рекомендуется теплое семейное направление без визы.
7. `eco-spring-hike` (`333`): если `travel_type=eco`, `season=spring`, `hobby=hiking`, то рекомендуется весенний экотур с пешими маршрутами.
8. `education-food-workshop` (`332`): если `travel_type=education`, `hobby=food`, то рекомендуется обучающий гастрономический тур с мастер-классами.
9. `dance-culture-festival` (`331`): если `hobby=dance`, `travel_type=culture`, то рекомендуется культурная поездка на фестивали и танцевальные мероприятия.
10. `museum-culture-grand-tour` (`330`): если `hobby=museum`, `travel_type=culture`, `budget_rub>=85000`, то рекомендуется насыщенный музейно-экскурсионный маршрут.
11. `hiking-winter-adventure` (`329`): если `hobby=hiking`, `season=winter`, `travel_type=active`, то рекомендуется зимний приключенческий маршрут с треккингом.
12. `couple-autumn-culture` (`328`): если `companions=couple`, `season=autumn`, `travel_type=culture`, то рекомендуется романтический культурный тур для пары.
13. `friends-winter-sport` (`327`): если `companions=friends`, `season=winter`, `travel_type=active`, то рекомендуется активный зимний тур для друзей.
14. `solo-active-adventure` (`326`): если `companions=solo`, `travel_type=active`, `trip_days>=6`, то рекомендуется активное путешествие с присоединением к организованным маршрутам.
15. `no-insurance-active-safe` (`325`): если `travel_type=active`, `insurance=no`, то рекомендуется безопасный активный маршрут внутри страны без экстремальных нагрузок.
16. `no-insurance-cold-safe` (`324`): если `climate=cold`, `insurance=no`, то рекомендуется короткая спокойная поездка без удаленных локаций.
17. `premium-visa-ready-relax` (`323`): если `visa_mode=visa_ready`, `travel_type=relax`, `service_level=premium`, то рекомендуется комфортный зарубежный отпуск с визой и высоким сервисом.

### Приоритеты 320-309

1. `summer-active-family` (`320`): если `climate=warm`, `season=summer`, `travel_type=active`, `companions=family`, то рекомендуется активный семейный отдых летом.
2. `winter-culture-couple` (`319`): если `climate=cold`, `season=winter`, `travel_type=culture`, `companions=couple`, то рекомендуется романтический зимний культурный тур.
3. `warm-eco-solo` (`318`): если `climate=warm`, `travel_type=eco`, `companions=solo`, `hobby=hiking`, то рекомендуется теплый эко-маршрут для одного.
4. `cold-adventure-friends` (`317`): если `climate=cold`, `travel_type=active`, `budget_rub>=120000`, `trip_days>=10`, `companions=friends`, `insurance=yes`, то рекомендуется зимнее приключение с друзьями.
5. `relax-long-visa` (`316`): если `climate=warm`, `travel_type=relax`, `budget_rub>=150000`, `trip_days>=14`, `service_level=premium`, `visa_mode=visa_ready`, `insurance=yes`, то рекомендуется долгий расслабленный отпуск с визой.
6. `culture-budget-solo` (`315`): если `travel_type=culture`, `30000<=budget_rub<60000`, `4<=trip_days<=6`, `companions=solo`, `service_level=economy`, `hobby=museum`, то рекомендуется бюджетный музейный тур для одного.
7. `family-roadtrip-mild` (`314`): если `climate=mild`, `season=summer`, `travel_type=mixed`, `50000<=budget_rub<90000`, `7<=trip_days<=9`, `companions=family`, `service_level=economy`, `insurance=no`, то рекомендуется семейное автопутешествие.
8. `health-premium-spring` (`313`): если `climate=mild`, `season=spring`, `travel_type=health`, `budget_rub>=100000`, `7<=trip_days<=10`, `companions=couple`, `service_level=premium`, `insurance=yes`, то рекомендуется весеннее оздоровление для пары.
9. `active-visa-free-short` (`312`): если `climate=warm`, `travel_type=active`, `budget_rub<80000`, `4<=trip_days<=7`, `companions=friends`, `service_level=economy`, `visa_mode=visa_free_only`, `insurance=no`, то рекомендуется активный безвизовый тур с друзьями.
10. `business-long-economy` (`311`): если `season=autumn`, `travel_type=business`, `50000<=budget_rub<80000`, `6<=trip_days<=10`, `companions=solo`, `service_level=economy`, то рекомендуется длительная деловая поездка с минимальными расходами.
11. `active-short-budget` (`310`): если `travel_type=active`, `budget_rub<100000`, `trip_days<=7`, то рекомендуется активный короткий тур по России или соседним направлениям.
12. `mixed-family-culture` (`310`): если `climate=mild`, `travel_type=mixed`, `5<=trip_days<=8`, `companions=family`, `service_level=standard`, `hobby=museum`, то рекомендуется семейный смешанный формат с экскурсиями и отдыхом.
13. `solo-eco-winter` (`309`): если `climate=cold`, `season=winter`, `travel_type=eco`, `60000<=budget_rub<100000`, `5<=trip_days<=7`, `companions=solo`, `service_level=standard`, `hobby=hiking`, `insurance=yes`, то рекомендуется зимний эко-тур в одиночку.

### Приоритеты 305-270

1. `family-mild-climate` (`305`): если `companions=family`, `climate=mild`, то рекомендуется семейный отдых в умеренном климате.
2. `budget-weekend-domestic` (`295`): если `budget_rub<50000`, `trip_days<=3`, то рекомендуется недорогая поездка на выходные по России.
3. `culture-short-citybreak` (`294`): если `travel_type=culture`, `trip_days<=5`, то рекомендуется короткий культурный тур по городам.
4. `relax-medium-resort` (`293`): если `travel_type=relax`, `70000<=budget_rub<130000`, `5<=trip_days<=10`, то рекомендуется стандартный курортный отдых средней длительности.
5. `health-short-retreat` (`292`): если `travel_type=health`, `trip_days<=8`, то рекомендуется короткая оздоровительная поездка.
6. `business-short-standard` (`291`): если `travel_type=business`, `trip_days<=4`, то рекомендуется короткая деловая поездка.
7. `eco-budget-trail` (`290`): если `travel_type=eco`, `budget_rub<90000`, то рекомендуется бюджетный экотур.
8. `mixed-week-combo` (`289`): если `travel_type=mixed`, `7<=trip_days<=10`, то рекомендуется комбинированный тур на неделю.
9. `long-culture-grand-tour` (`288`): если `travel_type=culture`, `trip_days>=10`, `budget_rub>=90000`, то рекомендуется длинный экскурсионный маршрут.
10. `long-active-expedition` (`287`): если `travel_type=active`, `trip_days>=12`, `budget_rub>=110000`, то рекомендуется активное путешествие экспедиционного типа.
11. `couple-relax-premium` (`286`): если `companions=couple`, `travel_type=relax`, `service_level=premium`, то рекомендуется премиальный романтический отдых для пары.
12. `friends-budget-roadtrip` (`285`): если `companions=friends`, `budget_rub<90000`, то рекомендуется бюджетное дорожное путешествие для друзей.
13. `family-culture-schoolbreak` (`284`): если `companions=family`, `travel_type=culture`, `trip_days<=7`, то рекомендуется короткая семейная культурная поездка.
14. `warm-summer-beach` (`283`): если `climate=warm`, `season=summer`, то рекомендуется летний морской отдых в теплом климате.
15. `cold-winter-relax` (`282`): если `climate=cold`, `season=winter`, `travel_type=relax`, то рекомендуется спокойный зимний отдых в холодном климате.
16. `mild-spring-city` (`281`): если `climate=mild`, `season=spring`, то рекомендуется весенний маршрут в умеренном климате.
17. `warm-autumn-gastro` (`280`): если `climate=warm`, `season=autumn`, `hobby=food`, то рекомендуется теплый осенний гастрономический тур.
18. `cold-short-culture` (`279`): если `climate=cold`, `travel_type=culture`, `trip_days<=4`, то рекомендуется короткая культурная поездка в холодный сезон.
19. `visa-free-short-trip` (`278`): если `visa_mode=visa_free_only`, `trip_days<=7`, то рекомендуется короткое безвизовое направление.
20. `visa-free-business-quick` (`277`): если `visa_mode=visa_free_only`, `travel_type=business`, `trip_days<=5`, то рекомендуется быстрая безвизовая деловая поездка.
21. `insurance-health-therapy` (`276`): если `insurance=yes`, `travel_type=health`, то рекомендуется оздоровительная поездка с медицинским блоком.
22. `service-premium-comfort` (`275`): если `service_level=premium`, `budget_rub>=120000`, то рекомендуется комфортная поездка с премиальным сервисом.
23. `service-economy-domestic` (`274`): если `service_level=economy`, `budget_rub<80000`, то рекомендуется экономичный маршрут внутри страны.
24. `service-standard-culture` (`273`): если `service_level=standard`, `travel_type=culture`, то рекомендуется культурный тур стандартного уровня.
25. `hobby-hiking-eco` (`272`): если `hobby=hiking`, `travel_type=eco`, то рекомендуется природный маршрут с треккингом.
26. `hobby-food-gastro` (`271`): если `hobby=food`, то рекомендуется гастрономическая поездка.
27. `hobby-museum-city` (`270`): если `hobby=museum`, то рекомендуется городская экскурсионная поездка с музеями.

### Приоритеты 260-243

1. `family-relax-tour` (`260`): если `companions=family`, `travel_type=relax`, то рекомендуется спокойный семейный отдых.
2. `friends-active-tour` (`259`): если `companions=friends`, `travel_type=active`, то рекомендуется активная поездка для друзей.
3. `business-general` (`250`): если `travel_type=business`, то рекомендуется общий деловой формат поездки.
4. `eco-general` (`249`): если `travel_type=eco`, то рекомендуется общий экологический тур.
5. `education-general` (`248`): если `travel_type=education`, то рекомендуется общий обучающий тур.
6. `health-general` (`247`): если `travel_type=health`, то рекомендуется общий оздоровительный отдых.
7. `culture-general` (`246`): если `travel_type=culture`, то рекомендуется общая культурно-познавательная поездка.
8. `relax-general` (`245`): если `travel_type=relax`, то рекомендуется общий спокойный отдых.
9. `active-general` (`244`): если `travel_type=active`, то рекомендуется общий активный формат поездки.
10. `mixed-general` (`243`): если `travel_type=mixed`, то рекомендуется общий смешанный формат путешествия.

### Fallback

`default-recommendation` (`-1000`): если ни одно предметное правило не было выбрано, возвращается рекомендация:

> Рекомендуется универсальный экскурсионный отдых по вашему бюджету и срокам.

## Замечания по текущей реализации

1. Реальное число предметных правил в `app/rules.py` равно `67`, поэтому старое описание про `50` правил устарело.
2. В explain-слое fallback тоже оформлен как правило с приоритетом `-1000`.
3. Правило `dance-culture-festival` существует в движке, но значение `hobby="dance"` отсутствует в `TRAVEL_FACTS`, поэтому из стандартной формы сайта это правило сейчас недостижимо.
