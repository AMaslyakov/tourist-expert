from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ValidatorKind = Literal["required", "number_range"]
FieldType = Literal["string", "integer", "select", "textarea", "submit"]
Operator = Literal["eq", "lt", "lte", "gt", "gte"]


@dataclass(frozen=True)
class ValidatorSpec:
    kind: ValidatorKind
    message: str | None = None
    min_value: int | None = None
    max_value: int | None = None


@dataclass(frozen=True)
class FactSpec:
    name: str
    label: str
    field_type: FieldType
    required: bool = False
    choices: tuple[tuple[str, str], ...] = ()
    validators: tuple[ValidatorSpec, ...] = ()
    ui: dict[str, Any] = field(default_factory=dict)
    fact_slot: str | None = None
    include_in_session: bool = True


@dataclass(frozen=True)
class ConditionSpec:
    slot: str
    op: Operator
    value: str | int


TRAVEL_FACTS: tuple[FactSpec, ...] = (
    FactSpec(
        name="season",
        label="Сезон поездки",
        field_type="select",
        required=True,
        choices=(
            ("any", "Без предпочтений"),
            ("spring", "Весна"),
            ("summer", "Лето"),
            ("autumn", "Осень"),
            ("winter", "Зима"),
        ),
        validators=(
            ValidatorSpec(kind="required", message="Выберите сезон поездки."),
        ),
        fact_slot="season",
    ),
    FactSpec(
        name="hobby",
        label="Увлечение",
        field_type="select",
        required=True,
        choices=(
            ("hiking", "Походы"),
            ("museum", "Музеи"),
            ("food", "Гастрономия"),
            ("any", "Без предпочтений"),
        ),
        validators=(
            ValidatorSpec(kind="required", message="Выберите увлечение."),
        ),
        fact_slot="hobby",
    ),
    FactSpec(
        name="budget_rub",
        label="Бюджет (руб.)",
        field_type="integer",
        required=True,
        validators=(
            ValidatorSpec(kind="required", message="Укажите бюджет."),
            ValidatorSpec(
                kind="number_range",
                min_value=1000,
                message="Бюджет должен быть не меньше 1000 руб.",
            ),
        ),
        ui={"min": 1000, "step": 1000, "placeholder": "Например: 120000"},
        fact_slot="budget_rub",
    ),
    FactSpec(
        name="trip_days",
        label="Длительность (дней)",
        field_type="integer",
        required=True,
        validators=(
            ValidatorSpec(kind="required", message="Укажите длительность поездки."),
            ValidatorSpec(
                kind="number_range",
                min_value=1,
                max_value=60,
                message="Допустимый диапазон: от 1 до 60 дней.",
            ),
        ),
        ui={"min": 1, "max": 60, "placeholder": "Например: 7"},
        fact_slot="trip_days",
    ),
    FactSpec(
        name="climate",
        label="Предпочитаемый климат",
        field_type="select",
        required=True,
        choices=(
            ("any", "Без предпочтений"),
            ("warm", "Теплый"),
            ("mild", "Умеренный"),
            ("cold", "Прохладный"),
        ),
        validators=(
            ValidatorSpec(kind="required", message="Выберите климат."),
        ),
        fact_slot="climate",
    ),
    FactSpec(
        name="travel_type",
        label="Тип отдыха",
        field_type="select",
        required=True,
        choices=(
            ("relax", "Спокойный"),
            ("active", "Активный"),
            ("mixed", "Смешанный"),
            ("culture", "Культурный"),
            ("health", "Оздоровительный"),
            ("business", "Деловой"),
            ("eco", "Экологический"),
            ("education", "Обучающий"),
        ),
        validators=(
            ValidatorSpec(kind="required", message="Выберите тип отдыха."),
        ),
        fact_slot="travel_type",
    ),
    FactSpec(
        name="companions",
        label="Состав поездки",
        field_type="select",
        required=True,
        choices=(
            ("solo", "Один"),
            ("couple", "Пара"),
            ("family", "Семья"),
            ("friends", "Друзья"),
        ),
        validators=(
            ValidatorSpec(kind="required", message="Выберите состав поездки."),
        ),
        fact_slot="companions",
    ),
    FactSpec(
        name="service_level",
        label="Уровень сервиса",
        field_type="select",
        required=True,
        choices=(
            ("economy", "Эконом"),
            ("standard", "Стандарт"),
            ("premium", "Премиум"),
        ),
        validators=(
            ValidatorSpec(kind="required", message="Выберите уровень сервиса."),
        ),
        fact_slot="service_level",
    ),
    FactSpec(
        name="visa_mode",
        label="Визовые ограничения",
        field_type="select",
        required=True,
        choices=(
            ("any", "Не важно"),
            ("visa_free_only", "Только без визы"),
            ("visa_ready", "Готов(а) оформить визу"),
        ),
        validators=(
            ValidatorSpec(kind="required", message="Укажите визовые ограничения."),
        ),
        fact_slot="visa_mode",
    ),
    FactSpec(
        name="insurance",
        label="Страховка",
        field_type="select",
        required=True,
        choices=(
            ("yes", "Страховка оформлена или будет оформлена"),
            ("no", "Без страховки"),
        ),
        validators=(
            ValidatorSpec(
                kind="required",
                message="Укажите, готовы ли вы оформить страховку.",
            ),
        ),
        fact_slot="insurance",
    ),
    FactSpec(
        name="notes",
        label="Дополнительные пожелания",
        field_type="textarea",
        ui={"placeholder": "Например: нужен пляж, мало пересадок, прямой рейс."},
    ),
    FactSpec(
        name="submit",
        label="Начать консультацию",
        field_type="submit",
        include_in_session=False,
    ),
)

DEFAULT_RECOMMENDATION = (
    "Рекомендуется универсальный экскурсионный отдых по вашему бюджету и срокам."
)
