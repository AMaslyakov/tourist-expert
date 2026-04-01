## Последний коммит (`487dcb5`) — изменения в `app`

- `app/rules.py`: база правил расширена с 4 до 56; добавлены новые сценарии (сезон, сервис, визы, страховка, новые типы туризма), добавлен `steps` в `EvaluationResult`, добавлен подробный `forward explain`.
- `app/knowledge.py`: добавлены факты `season`, `service_level`, `visa_mode`, `insurance`; расширен `travel_type` (`health`, `business`, `eco`, `education`).
- `app/__init__.py`: для обратного вывода используется `goal="*"`; в сохранение explain добавлено поле `forward.steps`.
