from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ValidatorKind = Literal["required", "number_range"]
FieldType = Literal["string", "integer", "select", "textarea", "submit"]
ClipType = Literal["INTEGER", "SYMBOL", "STRING"]
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
    clip_type: ClipType | None = None
    include_in_session: bool = True


@dataclass(frozen=True)
class ConditionSpec:
    slot: str
    op: Operator
    value: str | int


@dataclass(frozen=True)
class RuleSpec:
    name: str
    when: tuple[ConditionSpec, ...]
    recommendation: str
    priority: int


TRAVEL_FACTS: tuple[FactSpec, ...] = (
    FactSpec(
        name="departure_city",
        label="Город отправления",
        field_type="string",
        required=True,
        validators=(
            ValidatorSpec(kind="required", message="Укажите город отправления."),
        ),
        ui={"placeholder": "Например: Екатеринбург"},
    ),
    FactSpec(
        name="hobby",
        label="Увлечение",
        field_type="select",
        required=True,
        choices=(
            ("dance", "Танцы"),
            ("hiking", "Походы"),
            ("museum", "Музеи"),
            ("food", "Гастрономия"),
            ("any", "Без предпочтений"),
        ),
        validators=(
            ValidatorSpec(kind="required", message="Выберите увлечение."),
        ),
        fact_slot="hobby",
        clip_type="SYMBOL",
    ),

    FactSpec(
        name="insurance",
        label="Медецинская страховка",
        field_type="string",
        required=True,
        validators=(
          ValidatorSpec(kind="required", message="Укажите страховку"),
      ),
        ui={"placeholder": "Например: есть"},
      fact_slot="insurance",
      clip_type="STRING",
    )
    ,
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
        clip_type="INTEGER",
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
        clip_type="INTEGER",
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
        clip_type="SYMBOL",
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
        ),
        validators=(
            ValidatorSpec(kind="required", message="Выберите тип отдыха."),
        ),
        fact_slot="travel_type",
        clip_type="SYMBOL",
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
        clip_type="SYMBOL",
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


TRAVEL_RULES: tuple[RuleSpec, ...] = (
    RuleSpec(
        name="warm-relax-premium",
        priority=300,
        when=(
            ConditionSpec(slot="climate", op="eq", value="warm"),
            ConditionSpec(slot="travel_type", op="eq", value="relax"),
            ConditionSpec(slot="budget_rub", op="gte", value=100000),
        ),
        recommendation=(
            "Рекомендуется пляжный отдых в теплой стране с повышенным уровнем "
            "комфорта."
        ),
    ),
    RuleSpec(
        name="insurance-rule",
        priority=301,
        when=(
            ConditionSpec(slot="insurance", op="eq", value="есть"),
        ),
        recommendation=(
            "Рекомендуется любой отдых"
            ),
    ),
    RuleSpec(
        name="active-short-budget",
        priority=250,
        when=(
            ConditionSpec(slot="travel_type", op="eq", value="active"),
            ConditionSpec(slot="budget_rub", op="lt", value=100000),
            ConditionSpec(slot="trip_days", op="lte", value=7),
        ),
        recommendation=(
            "Рекомендуется активный короткий тур по России или соседним "
            "направлениям."
        ),
    ),
    RuleSpec(
        name="family-mild-climate",
        priority=220,
        when=(
            ConditionSpec(slot="companions", op="eq", value="family"),
            ConditionSpec(slot="climate", op="eq", value="mild"),
        ),
        recommendation=(
            "Рекомендуется семейный отдых в умеренном климате с короткими "
            "переездами."
        ),
    ),
    RuleSpec(
        name="hobby-dance-korea",
        priority=280,
        when=(
            ConditionSpec(slot="hobby", op="eq", value="dance"),
        ),
        recommendation="Рекомендуется поездка в Южную Корею.",
    ),
)

DEFAULT_RECOMMENDATION = (
    "Рекомендуется универсальный экскурсионный отдых по вашему бюджету и срокам."
)
