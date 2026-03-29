# Анализ предметной области экспертной системы «Консультант по путешествиям»

## 1. Цель и границы предметной области

Система решает задачу **предпоездочной консультации**: по фактам о пользователе и параметрах поездки выдаёт рекомендацию формата отдыха/направления.

В границы текущего домена входят:
- профиль и предпочтения туриста;
- ограничения поездки (бюджет, длительность, состав группы);
- часть факторов риска и готовности к поездке (например, страховка);
- формирование объяснимой рекомендации на основе продукционных правил.

Вне границ текущего прототипа:
- бронирование и оплата;
- визовая поддержка и документооборот;
- динамическая проверка цен/рейсов в реальном времени;
- сопровождение после начала поездки.

## 2. Нормативно-концептуальная база

Предметная область опирается на два уровня понятий:

1. **Правовой (РФ):** ст. 1 132-ФЗ задаёт базовые определения («туризм», «турист», «экскурсант», «туристский продукт»).
2. **Статистико-методологический (международный):** IRTS 2008 задаёт понятия «visitor», «tourism trip», «main purpose», «same-day visitor» и классификацию характеристик поездки.

Это позволяет разделять:
- юридические ограничения и состав турпродукта в РФ;
- универсальные признаки поездки, которые удобны для формализации в правилах.

## 3. Термины и определения

| Термин | Определение (кратко) | Значение для ЭС |
|---|---|---|
| Туризм | Временные выезды без извлечения дохода в месте пребывания | Базовый класс целевых сценариев консультации |
| Турист | Лицо, посещающее место временного пребывания на определённый срок/с ночёвкой | Центральный тип пользователя системы |
| Экскурсант | Посещение менее 24 часов без ночёвки | Граничный сценарий коротких поездок |
| Туристский продукт | Комплекс услуг за общую цену по договору | Основа рекомендаций «пакетного» типа |
| Visitor (IRTS) | Путешественник вне usual environment, до 1 года, не для трудоустройства у резидента места пребывания | Универсальное международное определение для модели фактов |
| Tourism trip | Поездка visitor-а, характеризуемая целью, длительностью, направлением и т.д. | Единица рассуждения в правилах |
| Main purpose | Цель, без которой поездка не состоялась бы | Ключ к выбору веток правил |
| Main destination | Место, центральное для решения о поездке | Нормализует логику по направлению |
| Same-day visitor | Посетитель без ночёвки | Влияет на класс рекомендаций и длительность |
| Salience | Приоритет правила в agenda (CLIPS) | Управление конфликтами между подходящими правилами |
| Forward chaining | Вывод от известных фактов к заключению | Базовый режим текущего прототипа |
| Backward chaining | Вывод от цели к недостающим фактам | Нужен для сценариев целевого (goal-driven) консультирования |
| Travel risk perception | Восприятие рисков (здоровье, криминал, политическая нестабильность и др.) влияет на выбор направления | Основа для расширения блока risk-правил |
| Travel health / evacuation insurance | Специализированные полисы на случай лечения и эвакуации за рубежом | Факт готовности и безопасности поездки |

## 4. Ключевые сущности предметной области

На уровне текущей модели (реестр `TRAVEL_FACTS`):

- Профиль и мотивация: `hobby`, `travel_type`.
- Ограничения поездки: `budget_rub`, `trip_days`.
- Контекст поездки: `companions`, `climate`, `departure_city`.
- Риск/подготовка: `insurance`.
- Свободные уточнения: `notes`.

Это соответствует литературным факторам выбора направления: цена/доступность, безопасность, климат/погода, инфраструктура и персональные характеристики туриста.

## 5. Особенности предметной области

1. **Многокритериальность.** Решение зависит от комбинации мотивации, бюджета, длительности, состава группы и климата.
2. **Сильная контекстность.** Одинаковый бюджет даёт разные рекомендации для solo/couple/family.
3. **Риск-чувствительность.** Восприятие рисков (здоровье, безопасность, политическая ситуация) меняет выбор направления и формата отдыха.
4. **Нормативная зависимость.** Для РФ важны юридические определения и состав турпродукта (актуальная редакция 132-ФЗ от 29.12.2025, вступившая в силу 01.03.2026).
5. **Требование объяснимости.** Для учебной экспертной системы важно сохранять цепочку сработавших правил и логику выбора.

## 6. Вывод в терминах требований проекта

### Прямой вывод

Интерпретация для проекта:
- на вход подаются пользовательские факты;
- движок активирует применимые правила;
- по приоритету (`salience`) выбирается итоговая рекомендация.

### Обратный вывод

Интерпретация для проекта:
- задаётся целевая гипотеза (например, «подходит семейный культурный тур»);
- система запрашивает/проверяет недостающие факты для доказательства или опровержения цели;
- строится цепочка, показывающая, какие факты были необходимы.

### Критерии полноты для учебного прототипа

- не менее 50 продукционных правил;
- минимум 2 примера прямого вывода (каждый: 51+ шаг, 2+ прохода);
- минимум 2 примера обратного вывода (каждый: 51+ шаг, 2+ прохода);
- сравнение производительности прямого и обратного вывода.

## 7. Текущее состояние и разрыв до требований

По текущему коду:
- в `TRAVEL_RULES` реализовано **5** предметных правил;
- есть механизм приоритетов и explain-вывода (`matched_rules`, `selected_rule`, `elapsed_ms`);
- обратный вывод как отдельный режим не реализован.

Следовательно, для соответствия критериям полноты нужно:
1. Расширить базу правил минимум до 50 (лучше 60+, чтобы покрыть граничные случаи).
2. Добавить слой goal-driven reasoning (или его имитацию через дерево целей и запрос недостающих фактов).
3. Добавить трассировку «шагов вывода» и «проходов» в структурированном виде для отчётных примеров.
4. Подготовить бенчмарки времени отдельно для прямого и обратного режимов.

## 8. Рекомендуемая декомпозиция правил (для достижения 50+)

- Блок A: бюджет x длительность x тип отдыха (12-16 правил).
- Блок B: состав группы x тип отдыха (10-12 правил).
- Блок C: климат x сезонность x активность (10-12 правил).
- Блок D: риск/страховка/ограничения (8-10 правил).
- Блок E: персональные интересы (хобби, культурные предпочтения) (8-10 правил).

Такая сетка даёт управляемое расширение без хаотичного роста конфликтов в agenda.

## Источники

1. Федеральный закон №132-ФЗ, ст. 1 (ред. от 29.12.2025, вступ. в силу с 01.03.2026): https://www.consultant.ru/document/cons_doc_LAW_12462/bb9e97fad9d14ac66df4b6e67c453d1be3b77b4c/
2. Изменения к определению «туристский продукт» и ст. 9.1 (553-ФЗ от 29.12.2025): https://www.consultant.ru/document/cons_doc_LAW_523101/3d0cac60971a511280cbba229d9b6329c07731f7/
3. UN IRTS 2008 (Statistical Papers Series M No.83/Rev.1): https://unstats.un.org/unsd/trade/irts/irts%202008%20unedited.pdf
4. CLIPS Basic Programming Guide (defrule, agenda, salience): https://www.clipsrules.net/documentation/v631/bpg631.pdf
5. Oracle Determinations Engine and the Inference Cycle (термины backward/forward chaining): https://docs.oracle.com/html/E79061_01/Content/Introducing%20Oracle%20Policy%20Modeling/Deter_Engine_and_infer_cycle.htm
6. CDC Yellow Book 2026, travel insurance guidance: https://www.cdc.gov/yellow-book/hcp/health-care-abroad/travel-insurance.html
7. MDPI (2023), factors in tourist decision-making: https://www.mdpi.com/2076-3387/13/10/215
8. Karl et al. (2020), risk salience in destination choice: https://pmc.ncbi.nlm.nih.gov/articles/PMC7494559/
9. clipspy on PyPI (актуальность и совместимость): https://pypi.org/project/clipspy/

## Приложение: расширенный список фактов и сущностей (100)

1. Туризм [132-ФЗ]
2. Турист [132-ФЗ]
3. Туристские ресурсы [132-ФЗ]
4. Туристская индустрия [132-ФЗ]
5. Туристский продукт [132-ФЗ]
6. Формирование туристского продукта [132-ФЗ]
7. Продвижение туристского продукта [132-ФЗ]
8. Реализация туристского продукта [132-ФЗ]
9. Туристская деятельность [132-ФЗ]
10. Туроператорская деятельность [132-ФЗ]
11. Турагентская деятельность [132-ФЗ]
12. Туроператор [132-ФЗ]
13. Турагент [132-ФЗ]
14. Заказчик туристского продукта [132-ФЗ]
15. Экскурсант [132-ФЗ]
16. Экскурсовод (гид) [132-ФЗ]
17. Гид-переводчик [132-ФЗ]
18. Инструктор-проводник [132-ФЗ]
19. Электронная путевка [132-ФЗ]
20. Экстренная помощь туристу [132-ФЗ]
21. Объединение туроператоров в сфере выездного туризма [132-ФЗ]
22. Общая цена туристского продукта в сфере выездного туризма [132-ФЗ]
23. Договор о реализации туристского продукта [132-ФЗ]
24. Средство размещения (как элемент турпродукта) [132-ФЗ]
25. Перевозка (как элемент турпродукта) [132-ФЗ]
26. Visitor (посетитель) [IRTS 2008]
27. Tourism trip (туристская поездка) [IRTS 2008]
28. Tourist (overnight visitor) [IRTS 2008]
29. Same-day visitor [IRTS 2008]
30. Usual environment [IRTS 2008]
31. Country of residence [IRTS 2008]
32. Place of usual residence [IRTS 2008]
33. Main destination [IRTS 2008]
34. Main purpose of trip [IRTS 2008]
35. Personal purpose [IRTS 2008]
36. Business and professional purpose [IRTS 2008]
37. Holidays, leisure and recreation [IRTS 2008]
38. Visiting friends and relatives [IRTS 2008]
39. Education and training [IRTS 2008]
40. Health and medical care [IRTS 2008]
41. Religion/pilgrimage [IRTS 2008]
42. Shopping purpose [IRTS 2008]
43. Transit purpose [IRTS 2008]
44. Other purpose [IRTS 2008]
45. Duration of trip [IRTS 2008]
46. Number of overnights [IRTS 2008]
47. Inbound tourism [IRTS 2008]
48. Outbound tourism [IRTS 2008]
49. Domestic tourism [IRTS 2008]
50. Internal tourism [IRTS 2008]
51. National tourism [IRTS 2008]
52. International tourism [IRTS 2008]
53. Tourism expenditure [IRTS 2008]
54. Inbound tourism expenditure [IRTS 2008]
55. Outbound tourism expenditure [IRTS 2008]
56. Domestic tourism expenditure [IRTS 2008]
57. Internal tourism expenditure [IRTS 2008]
58. National tourism expenditure [IRTS 2008]
59. Tourism characteristic products [IRTS 2008]
60. Internationally comparable tourism characteristic products [IRTS 2008]
61. Country-specific tourism characteristic products [IRTS 2008]
62. Tourism connected products [IRTS 2008]
63. Tourism industries [IRTS 2008]
64. Accommodation for visitors [IRTS 2008]
65. Food and beverage serving activities [IRTS 2008]
66. Passenger transport services [IRTS 2008]
67. Travel agencies and reservation services [IRTS 2008]
68. Cultural services [IRTS 2008]
69. Sports and recreational services [IRTS 2008]
70. Mode of transport for tourism trip [IRTS 2008]
71. Tourism Statistics Framework [UN Statistics]
72. Tourism Satellite Account (TSA:RMF) [UN Statistics]
73. Trip classification by purpose [UNSD Classification]
74. Product classification for tourism analysis [UNSD Classification]
75. Statistical unit: trip/visit [UNSD Classification]
76. Travel insurance (общее понятие) [CDC Yellow Book 2026]
77. Domestic health insurance abroad coverage [CDC Yellow Book 2026]
78. Travel disruption insurance [CDC Yellow Book 2026]
79. Travel health insurance [CDC Yellow Book 2026]
80. Medical evacuation insurance [CDC Yellow Book 2026]
81. Medevac [CDC Yellow Book 2026]
82. Repatriation to home-country facility [CDC Yellow Book 2026]
83. In-network providers [CDC Yellow Book 2026]
84. Preauthorization [CDC Yellow Book 2026]
85. Out-of-pocket payment at point of service [CDC Yellow Book 2026]
86. Reimbursement process [CDC Yellow Book 2026]
87. Coverage exclusions for high-risk activities [CDC Yellow Book 2026]
88. Coverage exclusions for preexisting conditions [CDC Yellow Book 2026]
89. Emergency support center 24/7/365 [CDC Yellow Book 2026]
90. Documentation of medical expenses [CDC Yellow Book 2026]
91. Knowledge base [CLIPS]
92. Working memory facts [CLIPS]
93. Deftemplate [CLIPS]
94. Defrule [CLIPS]
95. Agenda [CLIPS]
96. Salience [CLIPS]
97. Conflict resolution [CLIPS]
98. Pattern matching [CLIPS]
99. Forward chaining inference [CLIPS/Oracle]
100. Backward chaining inference [Oracle]
