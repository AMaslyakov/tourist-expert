from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Any, Callable, Literal, Mapping

from app.experta_compat import patch_experta_compat
from app.knowledge import ConditionSpec, DEFAULT_RECOMMENDATION, TRAVEL_FACTS

patch_experta_compat()

from experta import MATCH, TEST, Fact, KnowledgeEngine, Rule  # noqa: E402

if TYPE_CHECKING:
    from flask import Flask


DEFAULT_RULE_NAME = "default-recommendation"


@dataclass(frozen=True)
class RuleMetadata:
    name: str
    priority: int
    recommendation: str
    conditions: tuple[ConditionSpec, ...]


@dataclass(frozen=True)
class EvaluationResult:
    recommendation: str
    matched_rules: tuple[str, ...]
    selected_rule: str
    elapsed_ms: float
    passes: int
    steps: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class BackwardResult:
    goal: str
    achieved: bool
    selected_rule: str | None
    matched_rules: tuple[str, ...]
    recommendation: str | None
    elapsed_ms: float
    passes: int
    steps: tuple[dict[str, Any], ...]
    proof: dict[str, Any] | None = None


def _register_rule(
    *,
    name: str,
    priority: int,
    recommendation: str,
    conditions: tuple[ConditionSpec, ...],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    metadata = RuleMetadata(
        name=name,
        priority=priority,
        recommendation=recommendation,
        conditions=conditions,
    )

    def decorator(rule_callable: Callable[..., Any]) -> Callable[..., Any]:
        # Keep metadata priority and experta conflict priority in sync.
        setattr(rule_callable, "salience", priority)
        setattr(rule_callable, "_travel_rule_metadata", metadata)
        return rule_callable

    return decorator


def _collect_rule_metadata(engine_class: type[KnowledgeEngine]) -> dict[str, RuleMetadata]:
    metadata_by_name: dict[str, RuleMetadata] = {}
    for attr_name in dir(engine_class):
        attr = getattr(engine_class, attr_name)
        metadata = getattr(attr, "_travel_rule_metadata", None)
        if isinstance(metadata, RuleMetadata):
            metadata_by_name[metadata.name] = metadata

    metadata_by_name[DEFAULT_RULE_NAME] = RuleMetadata(
        name=DEFAULT_RULE_NAME,
        priority=-1000,
        recommendation=DEFAULT_RECOMMENDATION,
        conditions=(),
    )
    return metadata_by_name


def _sorted_rules(metadata: Mapping[str, RuleMetadata]) -> list[RuleMetadata]:
    return sorted(
        (
            item
            for item in metadata.values()
            if item.name != DEFAULT_RULE_NAME
        ),
        key=lambda item: item.priority,
        reverse=True,
    )


def _apply_operator(op: Literal["eq", "lt", "lte", "gt", "gte"], left: Any, right: Any) -> bool:
    if op == "eq":
        return left == right
    if op == "lt":
        return left < right
    if op == "lte":
        return left <= right
    if op == "gt":
        return left > right
    if op == "gte":
        return left >= right
    raise ValueError(f"Unsupported operator: {op}")


def _condition_is_satisfied(condition: ConditionSpec, known_facts: Mapping[str, Any]) -> bool:
    if condition.slot not in known_facts:
        return False
    return _apply_operator(condition.op, known_facts[condition.slot], condition.value)


class TravelInput(Fact):
    """Input facts for travel recommendation inference."""


class _TravelExpertEngine(KnowledgeEngine):
    def __init__(self) -> None:
        super().__init__()
        self.rule_metadata = _collect_rule_metadata(self.__class__)
        self.reset_runtime_state()

    def reset_runtime_state(self) -> None:
        self.matched_rules: list[str] = []
        self.selected_rule: str | None = None
        self.selected_priority = float("-inf")
        self.recommendation = DEFAULT_RECOMMENDATION

    def register_match(self, rule_name: str) -> None:
        metadata = self.rule_metadata[rule_name]
        self.matched_rules.append(rule_name)
        if metadata.priority > self.selected_priority:
            self.selected_priority = metadata.priority
            self.selected_rule = metadata.name
            self.recommendation = metadata.recommendation

    @_register_rule(
        name="warm-relax-premium",
        priority=340,
        recommendation=(
            "Рекомендуется пляжный отдых в теплой стране с повышенным уровнем "
            "комфорта."
        ),
        conditions=(
            ConditionSpec(slot="climate", op="eq", value="warm"),
            ConditionSpec(slot="travel_type", op="eq", value="relax"),
            ConditionSpec(slot="budget_rub", op="gte", value=100000),
        ),
    )
    @Rule(
        TravelInput(climate="warm", travel_type="relax", budget_rub=MATCH.budget),
        TEST(lambda budget: budget >= 100000),
    )
    def rule_warm_relax_premium(self, budget: int) -> None:  # noqa: ARG002
        self.register_match("warm-relax-premium")

    @_register_rule(
        name="summer-family-beach",
        priority=338,
        recommendation=(
            "Рекомендуется семейный летний пляжный отдых с мягким графиком и "
            "короткими переездами."
        ),
        conditions=(
            ConditionSpec(slot="season", op="eq", value="summer"),
            ConditionSpec(slot="climate", op="eq", value="warm"),
            ConditionSpec(slot="companions", op="eq", value="family"),
        ),
    )
    @Rule(TravelInput(season="summer", climate="warm", companions="family"))
    def rule_summer_family_beach(self) -> None:
        self.register_match("summer-family-beach")

    @_register_rule(
        name="winter-active-ski",
        priority=337,
        recommendation=(
            "Рекомендуется зимний активный тур с горнолыжным курортом или "
            "снежными маршрутами."
        ),
        conditions=(
            ConditionSpec(slot="season", op="eq", value="winter"),
            ConditionSpec(slot="climate", op="eq", value="cold"),
            ConditionSpec(slot="travel_type", op="eq", value="active"),
        ),
    )
    @Rule(TravelInput(season="winter", climate="cold", travel_type="active"))
    def rule_winter_active_ski(self) -> None:
        self.register_match("winter-active-ski")

    @_register_rule(
        name="family-health-insured",
        priority=336,
        recommendation=(
            "Рекомендуется семейная оздоровительная программа в санаторном "
            "формате с оформленной страховкой."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="family"),
            ConditionSpec(slot="travel_type", op="eq", value="health"),
            ConditionSpec(slot="insurance", op="eq", value="yes"),
        ),
    )
    @Rule(TravelInput(companions="family", travel_type="health", insurance="yes"))
    def rule_family_health_insured(self) -> None:
        self.register_match("family-health-insured")

    @_register_rule(
        name="business-premium-city",
        priority=335,
        recommendation=(
            "Рекомендуется деловая поездка в крупный город с центральным "
            "отелем и премиальным уровнем сервиса."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="business"),
            ConditionSpec(slot="service_level", op="eq", value="premium"),
            ConditionSpec(slot="budget_rub", op="gte", value=90000),
        ),
    )
    @Rule(
        TravelInput(
            travel_type="business",
            service_level="premium",
            budget_rub=MATCH.budget,
        ),
        TEST(lambda budget: budget >= 90000),
    )
    def rule_business_premium_city(self, budget: int) -> None:  # noqa: ARG002
        self.register_match("business-premium-city")

    @_register_rule(
        name="visa-free-family-sea",
        priority=334,
        recommendation=(
            "Рекомендуется теплое семейное направление без визы с простой "
            "логистикой и морским отдыхом."
        ),
        conditions=(
            ConditionSpec(slot="visa_mode", op="eq", value="visa_free_only"),
            ConditionSpec(slot="companions", op="eq", value="family"),
            ConditionSpec(slot="climate", op="eq", value="warm"),
        ),
    )
    @Rule(
        TravelInput(
            visa_mode="visa_free_only",
            companions="family",
            climate="warm",
        ),
    )
    def rule_visa_free_family_sea(self) -> None:
        self.register_match("visa-free-family-sea")

    @_register_rule(
        name="eco-spring-hike",
        priority=333,
        recommendation=(
            "Рекомендуется весенний экотур с пешими маршрутами, национальными "
            "парками и умеренной нагрузкой."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="eco"),
            ConditionSpec(slot="season", op="eq", value="spring"),
            ConditionSpec(slot="hobby", op="eq", value="hiking"),
        ),
    )
    @Rule(TravelInput(travel_type="eco", season="spring", hobby="hiking"))
    def rule_eco_spring_hike(self) -> None:
        self.register_match("eco-spring-hike")

    @_register_rule(
        name="education-food-workshop",
        priority=332,
        recommendation=(
            "Рекомендуется обучающий гастрономический тур с мастер-классами, "
            "дегустациями и местной кухней."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="education"),
            ConditionSpec(slot="hobby", op="eq", value="food"),
        ),
    )
    @Rule(TravelInput(travel_type="education", hobby="food"))
    def rule_education_food_workshop(self) -> None:
        self.register_match("education-food-workshop")

    @_register_rule(
        name="dance-culture-festival",
        priority=331,
        recommendation=(
            "Рекомендуется культурная поездка на фестивали и танцевальные "
            "мероприятия."
        ),
        conditions=(
            ConditionSpec(slot="hobby", op="eq", value="dance"),
            ConditionSpec(slot="travel_type", op="eq", value="culture"),
        ),
    )
    @Rule(TravelInput(hobby="dance", travel_type="culture"))
    def rule_dance_culture_festival(self) -> None:
        self.register_match("dance-culture-festival")

    @_register_rule(
        name="museum-culture-grand-tour",
        priority=330,
        recommendation=(
            "Рекомендуется насыщенный музейно-экскурсионный маршрут по "
            "нескольким городам."
        ),
        conditions=(
            ConditionSpec(slot="hobby", op="eq", value="museum"),
            ConditionSpec(slot="travel_type", op="eq", value="culture"),
            ConditionSpec(slot="budget_rub", op="gte", value=85000),
        ),
    )
    @Rule(
        TravelInput(hobby="museum", travel_type="culture", budget_rub=MATCH.budget),
        TEST(lambda budget: budget >= 85000),
    )
    def rule_museum_culture_grand_tour(self, budget: int) -> None:  # noqa: ARG002
        self.register_match("museum-culture-grand-tour")

    @_register_rule(
        name="hiking-winter-adventure",
        priority=329,
        recommendation=(
            "Рекомендуется зимний приключенческий маршрут с треккингом и "
            "сопровождением инструкторов."
        ),
        conditions=(
            ConditionSpec(slot="hobby", op="eq", value="hiking"),
            ConditionSpec(slot="season", op="eq", value="winter"),
            ConditionSpec(slot="travel_type", op="eq", value="active"),
        ),
    )
    @Rule(TravelInput(hobby="hiking", season="winter", travel_type="active"))
    def rule_hiking_winter_adventure(self) -> None:
        self.register_match("hiking-winter-adventure")

    @_register_rule(
        name="couple-autumn-culture",
        priority=328,
        recommendation=(
            "Рекомендуется романтический культурный city-break для пары в "
            "бархатный сезон."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="couple"),
            ConditionSpec(slot="season", op="eq", value="autumn"),
            ConditionSpec(slot="travel_type", op="eq", value="culture"),
        ),
    )
    @Rule(
        TravelInput(companions="couple", season="autumn", travel_type="culture"),
    )
    def rule_couple_autumn_culture(self) -> None:
        self.register_match("couple-autumn-culture")

    @_register_rule(
        name="friends-winter-sport",
        priority=327,
        recommendation=(
            "Рекомендуется активный зимний тур для компании друзей со спортом "
            "и насыщенным вечерним досугом."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="friends"),
            ConditionSpec(slot="season", op="eq", value="winter"),
            ConditionSpec(slot="travel_type", op="eq", value="active"),
        ),
    )
    @Rule(
        TravelInput(companions="friends", season="winter", travel_type="active"),
    )
    def rule_friends_winter_sport(self) -> None:
        self.register_match("friends-winter-sport")

    @_register_rule(
        name="solo-active-adventure",
        priority=326,
        recommendation=(
            "Рекомендуется solo-путешествие с активной программой и "
            "присоединением к организованным маршрутам."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="solo"),
            ConditionSpec(slot="travel_type", op="eq", value="active"),
            ConditionSpec(slot="trip_days", op="gte", value=6),
        ),
    )
    @Rule(
        TravelInput(companions="solo", travel_type="active", trip_days=MATCH.days),
        TEST(lambda days: days >= 6),
    )
    def rule_solo_active_adventure(self, days: int) -> None:  # noqa: ARG002
        self.register_match("solo-active-adventure")

    @_register_rule(
        name="no-insurance-active-safe",
        priority=325,
        recommendation=(
            "Без страховки лучше выбрать безопасный активный маршрут внутри "
            "страны без экстремальных нагрузок."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="active"),
            ConditionSpec(slot="insurance", op="eq", value="no"),
        ),
    )
    @Rule(TravelInput(travel_type="active", insurance="no"))
    def rule_no_insurance_active_safe(self) -> None:
        self.register_match("no-insurance-active-safe")

    @_register_rule(
        name="no-insurance-cold-safe",
        priority=324,
        recommendation=(
            "Без страховки и при выборе холодного климата лучше ограничиться "
            "короткой спокойной поездкой без удаленных локаций."
        ),
        conditions=(
            ConditionSpec(slot="climate", op="eq", value="cold"),
            ConditionSpec(slot="insurance", op="eq", value="no"),
        ),
    )
    @Rule(TravelInput(climate="cold", insurance="no"))
    def rule_no_insurance_cold_safe(self) -> None:
        self.register_match("no-insurance-cold-safe")

    @_register_rule(
        name="premium-visa-ready-relax",
        priority=323,
        recommendation=(
            "Рекомендуется комфортный зарубежный отпуск: вы готовы к визе и "
            "ориентированы на высокий сервис."
        ),
        conditions=(
            ConditionSpec(slot="visa_mode", op="eq", value="visa_ready"),
            ConditionSpec(slot="travel_type", op="eq", value="relax"),
            ConditionSpec(slot="service_level", op="eq", value="premium"),
        ),
    )
    @Rule(
        TravelInput(
            visa_mode="visa_ready",
            travel_type="relax",
            service_level="premium",
        ),
    )
    def rule_premium_visa_ready_relax(self) -> None:
        self.register_match("premium-visa-ready-relax")

    @_register_rule(
        name="active-short-budget",
        priority=310,
        recommendation=(
            "Рекомендуется активный короткий тур по России или соседним "
            "направлениям."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="active"),
            ConditionSpec(slot="budget_rub", op="lt", value=100000),
            ConditionSpec(slot="trip_days", op="lte", value=7),
        ),
    )
    @Rule(
        TravelInput(travel_type="active", budget_rub=MATCH.budget, trip_days=MATCH.days),
        TEST(lambda budget, days: budget < 100000 and days <= 7),
    )
    def rule_active_short_budget(self, budget: int, days: int) -> None:  # noqa: ARG002
        self.register_match("active-short-budget")

    @_register_rule(
        name="family-mild-climate",
        priority=305,
        recommendation=(
            "Рекомендуется семейный отдых в умеренном климате с короткими "
            "переездами."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="family"),
            ConditionSpec(slot="climate", op="eq", value="mild"),
        ),
    )
    @Rule(TravelInput(companions="family", climate="mild"))
    def rule_family_mild_climate(self) -> None:
        self.register_match("family-mild-climate")

    @_register_rule(
        name="budget-weekend-domestic",
        priority=295,
        recommendation=(
            "Рекомендуется недорогая поездка на выходные по России с простой "
            "логистикой."
        ),
        conditions=(
            ConditionSpec(slot="budget_rub", op="lt", value=50000),
            ConditionSpec(slot="trip_days", op="lte", value=3),
        ),
    )
    @Rule(
        TravelInput(budget_rub=MATCH.budget, trip_days=MATCH.days),
        TEST(lambda budget, days: budget < 50000 and days <= 3),
    )
    def rule_budget_weekend_domestic(self, budget: int, days: int) -> None:  # noqa: ARG002
        self.register_match("budget-weekend-domestic")

    @_register_rule(
        name="culture-short-citybreak",
        priority=294,
        recommendation=(
            "Рекомендуется короткий культурный city-break с музеями, "
            "экскурсиями и вечерними прогулками."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="culture"),
            ConditionSpec(slot="trip_days", op="lte", value=5),
        ),
    )
    @Rule(
        TravelInput(travel_type="culture", trip_days=MATCH.days),
        TEST(lambda days: days <= 5),
    )
    def rule_culture_short_citybreak(self, days: int) -> None:  # noqa: ARG002
        self.register_match("culture-short-citybreak")

    @_register_rule(
        name="relax-medium-resort",
        priority=293,
        recommendation=(
            "Рекомендуется стандартный курортный отдых средней длительности с "
            "понятным бюджетом."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="relax"),
            ConditionSpec(slot="budget_rub", op="gte", value=70000),
            ConditionSpec(slot="budget_rub", op="lt", value=130000),
            ConditionSpec(slot="trip_days", op="gte", value=5),
            ConditionSpec(slot="trip_days", op="lte", value=10),
        ),
    )
    @Rule(
        TravelInput(travel_type="relax", budget_rub=MATCH.budget, trip_days=MATCH.days),
        TEST(lambda budget, days: 70000 <= budget < 130000 and 5 <= days <= 10),
    )
    def rule_relax_medium_resort(self, budget: int, days: int) -> None:  # noqa: ARG002
        self.register_match("relax-medium-resort")

    @_register_rule(
        name="health-short-retreat",
        priority=292,
        recommendation=(
            "Рекомендуется короткая оздоровительная поездка с восстановительным "
            "режимом и спокойным расписанием."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="health"),
            ConditionSpec(slot="trip_days", op="lte", value=8),
        ),
    )
    @Rule(
        TravelInput(travel_type="health", trip_days=MATCH.days),
        TEST(lambda days: days <= 8),
    )
    def rule_health_short_retreat(self, days: int) -> None:  # noqa: ARG002
        self.register_match("health-short-retreat")

    @_register_rule(
        name="business-short-standard",
        priority=291,
        recommendation=(
            "Рекомендуется короткая деловая поездка с четким графиком и "
            "удобным размещением."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="business"),
            ConditionSpec(slot="trip_days", op="lte", value=4),
        ),
    )
    @Rule(
        TravelInput(travel_type="business", trip_days=MATCH.days),
        TEST(lambda days: days <= 4),
    )
    def rule_business_short_standard(self, days: int) -> None:  # noqa: ARG002
        self.register_match("business-short-standard")

    @_register_rule(
        name="eco-budget-trail",
        priority=290,
        recommendation=(
            "Рекомендуется бюджетный экотур с природными маршрутами, базовой "
            "инфраструктурой и упором на впечатления."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="eco"),
            ConditionSpec(slot="budget_rub", op="lt", value=90000),
        ),
    )
    @Rule(
        TravelInput(travel_type="eco", budget_rub=MATCH.budget),
        TEST(lambda budget: budget < 90000),
    )
    def rule_eco_budget_trail(self, budget: int) -> None:  # noqa: ARG002
        self.register_match("eco-budget-trail")

    @_register_rule(
        name="mixed-week-combo",
        priority=289,
        recommendation=(
            "Рекомендуется комбинированный тур на неделю: часть программы "
            "спокойная, часть активная или экскурсионная."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="mixed"),
            ConditionSpec(slot="trip_days", op="gte", value=7),
            ConditionSpec(slot="trip_days", op="lte", value=10),
        ),
    )
    @Rule(
        TravelInput(travel_type="mixed", trip_days=MATCH.days),
        TEST(lambda days: 7 <= days <= 10),
    )
    def rule_mixed_week_combo(self, days: int) -> None:  # noqa: ARG002
        self.register_match("mixed-week-combo")

    @_register_rule(
        name="long-culture-grand-tour",
        priority=288,
        recommendation=(
            "Рекомендуется длинный экскурсионный маршрут по нескольким "
            "городам с насыщенной программой."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="culture"),
            ConditionSpec(slot="trip_days", op="gte", value=10),
            ConditionSpec(slot="budget_rub", op="gte", value=90000),
        ),
    )
    @Rule(
        TravelInput(travel_type="culture", trip_days=MATCH.days, budget_rub=MATCH.budget),
        TEST(lambda days, budget: days >= 10 and budget >= 90000),
    )
    def rule_long_culture_grand_tour(self, days: int, budget: int) -> None:  # noqa: ARG002
        self.register_match("long-culture-grand-tour")

    @_register_rule(
        name="long-active-expedition",
        priority=287,
        recommendation=(
            "Рекомендуется длительное активное путешествие или экспедиционный "
            "маршрут с хорошим запасом бюджета."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="active"),
            ConditionSpec(slot="trip_days", op="gte", value=12),
            ConditionSpec(slot="budget_rub", op="gte", value=110000),
        ),
    )
    @Rule(
        TravelInput(travel_type="active", trip_days=MATCH.days, budget_rub=MATCH.budget),
        TEST(lambda days, budget: days >= 12 and budget >= 110000),
    )
    def rule_long_active_expedition(self, days: int, budget: int) -> None:  # noqa: ARG002
        self.register_match("long-active-expedition")

    @_register_rule(
        name="couple-relax-premium",
        priority=286,
        recommendation=(
            "Рекомендуется премиальный романтический отдых для пары с акцентом "
            "на комфорт и приватность."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="couple"),
            ConditionSpec(slot="travel_type", op="eq", value="relax"),
            ConditionSpec(slot="service_level", op="eq", value="premium"),
        ),
    )
    @Rule(
        TravelInput(companions="couple", travel_type="relax", service_level="premium"),
    )
    def rule_couple_relax_premium(self) -> None:
        self.register_match("couple-relax-premium")

    @_register_rule(
        name="friends-budget-roadtrip",
        priority=285,
        recommendation=(
            "Рекомендуется бюджетный road-trip или насыщенный маршрут для "
            "компании друзей."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="friends"),
            ConditionSpec(slot="budget_rub", op="lt", value=90000),
        ),
    )
    @Rule(
        TravelInput(companions="friends", budget_rub=MATCH.budget),
        TEST(lambda budget: budget < 90000),
    )
    def rule_friends_budget_roadtrip(self, budget: int) -> None:  # noqa: ARG002
        self.register_match("friends-budget-roadtrip")

    @_register_rule(
        name="family-culture-schoolbreak",
        priority=284,
        recommendation=(
            "Рекомендуется короткая семейная культурная поездка на каникулы с "
            "понятной программой для детей и взрослых."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="family"),
            ConditionSpec(slot="travel_type", op="eq", value="culture"),
            ConditionSpec(slot="trip_days", op="lte", value=7),
        ),
    )
    @Rule(
        TravelInput(companions="family", travel_type="culture", trip_days=MATCH.days),
        TEST(lambda days: days <= 7),
    )
    def rule_family_culture_schoolbreak(self, days: int) -> None:  # noqa: ARG002
        self.register_match("family-culture-schoolbreak")

    @_register_rule(
        name="warm-summer-beach",
        priority=283,
        recommendation=(
            "Рекомендуется летний морской отдых в теплом климате."
        ),
        conditions=(
            ConditionSpec(slot="climate", op="eq", value="warm"),
            ConditionSpec(slot="season", op="eq", value="summer"),
        ),
    )
    @Rule(TravelInput(climate="warm", season="summer"))
    def rule_warm_summer_beach(self) -> None:
        self.register_match("warm-summer-beach")

    @_register_rule(
        name="cold-winter-relax",
        priority=282,
        recommendation=(
            "Рекомендуется спокойный зимний отдых в холодном климате: спа, "
            "термальные комплексы или северные отели."
        ),
        conditions=(
            ConditionSpec(slot="climate", op="eq", value="cold"),
            ConditionSpec(slot="season", op="eq", value="winter"),
            ConditionSpec(slot="travel_type", op="eq", value="relax"),
        ),
    )
    @Rule(TravelInput(climate="cold", season="winter", travel_type="relax"))
    def rule_cold_winter_relax(self) -> None:
        self.register_match("cold-winter-relax")

    @_register_rule(
        name="mild-spring-city",
        priority=281,
        recommendation=(
            "Рекомендуется весенний маршрут в умеренном климате: прогулки, "
            "экскурсии и легкая городская программа."
        ),
        conditions=(
            ConditionSpec(slot="climate", op="eq", value="mild"),
            ConditionSpec(slot="season", op="eq", value="spring"),
        ),
    )
    @Rule(TravelInput(climate="mild", season="spring"))
    def rule_mild_spring_city(self) -> None:
        self.register_match("mild-spring-city")

    @_register_rule(
        name="warm-autumn-gastro",
        priority=280,
        recommendation=(
            "Рекомендуется теплый осенний гастрономический тур с рынками, "
            "ресторанами и локальными дегустациями."
        ),
        conditions=(
            ConditionSpec(slot="climate", op="eq", value="warm"),
            ConditionSpec(slot="season", op="eq", value="autumn"),
            ConditionSpec(slot="hobby", op="eq", value="food"),
        ),
    )
    @Rule(TravelInput(climate="warm", season="autumn", hobby="food"))
    def rule_warm_autumn_gastro(self) -> None:
        self.register_match("warm-autumn-gastro")

    @_register_rule(
        name="cold-short-culture",
        priority=279,
        recommendation=(
            "Рекомендуется короткая культурная поездка в холодный сезон без "
            "сложной логистики и перегрузки."
        ),
        conditions=(
            ConditionSpec(slot="climate", op="eq", value="cold"),
            ConditionSpec(slot="travel_type", op="eq", value="culture"),
            ConditionSpec(slot="trip_days", op="lte", value=4),
        ),
    )
    @Rule(
        TravelInput(climate="cold", travel_type="culture", trip_days=MATCH.days),
        TEST(lambda days: days <= 4),
    )
    def rule_cold_short_culture(self, days: int) -> None:  # noqa: ARG002
        self.register_match("cold-short-culture")

    @_register_rule(
        name="visa-free-short-trip",
        priority=278,
        recommendation=(
            "Рекомендуется короткое безвизовое направление, чтобы не тратить "
            "время на подготовку документов."
        ),
        conditions=(
            ConditionSpec(slot="visa_mode", op="eq", value="visa_free_only"),
            ConditionSpec(slot="trip_days", op="lte", value=7),
        ),
    )
    @Rule(
        TravelInput(visa_mode="visa_free_only", trip_days=MATCH.days),
        TEST(lambda days: days <= 7),
    )
    def rule_visa_free_short_trip(self, days: int) -> None:  # noqa: ARG002
        self.register_match("visa-free-short-trip")

    @_register_rule(
        name="visa-free-business-quick",
        priority=277,
        recommendation=(
            "Рекомендуется быстрая безвизовая деловая поездка с минимальными "
            "организационными рисками."
        ),
        conditions=(
            ConditionSpec(slot="visa_mode", op="eq", value="visa_free_only"),
            ConditionSpec(slot="travel_type", op="eq", value="business"),
            ConditionSpec(slot="trip_days", op="lte", value=5),
        ),
    )
    @Rule(
        TravelInput(
            visa_mode="visa_free_only",
            travel_type="business",
            trip_days=MATCH.days,
        ),
        TEST(lambda days: days <= 5),
    )
    def rule_visa_free_business_quick(self, days: int) -> None:  # noqa: ARG002
        self.register_match("visa-free-business-quick")

    @_register_rule(
        name="insurance-health-therapy",
        priority=276,
        recommendation=(
            "Рекомендуется оздоровительная поездка с медицинским блоком: "
            "наличие страховки делает такой формат безопаснее."
        ),
        conditions=(
            ConditionSpec(slot="insurance", op="eq", value="yes"),
            ConditionSpec(slot="travel_type", op="eq", value="health"),
        ),
    )
    @Rule(TravelInput(insurance="yes", travel_type="health"))
    def rule_insurance_health_therapy(self) -> None:
        self.register_match("insurance-health-therapy")

    @_register_rule(
        name="service-premium-comfort",
        priority=275,
        recommendation=(
            "Рекомендуется комфортная поездка с премиальным сервисом и "
            "повышенным уровнем удобства."
        ),
        conditions=(
            ConditionSpec(slot="service_level", op="eq", value="premium"),
            ConditionSpec(slot="budget_rub", op="gte", value=120000),
        ),
    )
    @Rule(
        TravelInput(service_level="premium", budget_rub=MATCH.budget),
        TEST(lambda budget: budget >= 120000),
    )
    def rule_service_premium_comfort(self, budget: int) -> None:  # noqa: ARG002
        self.register_match("service-premium-comfort")

    @_register_rule(
        name="service-economy-domestic",
        priority=274,
        recommendation=(
            "Рекомендуется экономичный маршрут внутри страны с упором на цену "
            "и базовый набор услуг."
        ),
        conditions=(
            ConditionSpec(slot="service_level", op="eq", value="economy"),
            ConditionSpec(slot="budget_rub", op="lt", value=80000),
        ),
    )
    @Rule(
        TravelInput(service_level="economy", budget_rub=MATCH.budget),
        TEST(lambda budget: budget < 80000),
    )
    def rule_service_economy_domestic(self, budget: int) -> None:  # noqa: ARG002
        self.register_match("service-economy-domestic")

    @_register_rule(
        name="service-standard-culture",
        priority=273,
        recommendation=(
            "Рекомендуется культурный тур стандартного уровня: без излишней "
            "роскоши, но с комфортным размещением."
        ),
        conditions=(
            ConditionSpec(slot="service_level", op="eq", value="standard"),
            ConditionSpec(slot="travel_type", op="eq", value="culture"),
        ),
    )
    @Rule(TravelInput(service_level="standard", travel_type="culture"))
    def rule_service_standard_culture(self) -> None:
        self.register_match("service-standard-culture")

    @_register_rule(
        name="hobby-hiking-eco",
        priority=272,
        recommendation=(
            "Рекомендуется природный маршрут с треккингом, смотровыми точками "
            "и умеренной физической нагрузкой."
        ),
        conditions=(
            ConditionSpec(slot="hobby", op="eq", value="hiking"),
            ConditionSpec(slot="travel_type", op="eq", value="eco"),
        ),
    )
    @Rule(TravelInput(hobby="hiking", travel_type="eco"))
    def rule_hobby_hiking_eco(self) -> None:
        self.register_match("hobby-hiking-eco")

    @_register_rule(
        name="hobby-food-gastro",
        priority=271,
        recommendation=(
            "Рекомендуется гастрономическая поездка с рынками, дегустациями и "
            "локальной кухней."
        ),
        conditions=(
            ConditionSpec(slot="hobby", op="eq", value="food"),
        ),
    )
    @Rule(TravelInput(hobby="food"))
    def rule_hobby_food_gastro(self) -> None:
        self.register_match("hobby-food-gastro")

    @_register_rule(
        name="hobby-museum-city",
        priority=270,
        recommendation=(
            "Рекомендуется городская экскурсионная поездка с музеями, "
            "историческими центрами и выставками."
        ),
        conditions=(
            ConditionSpec(slot="hobby", op="eq", value="museum"),
        ),
    )
    @Rule(TravelInput(hobby="museum"))
    def rule_hobby_museum_city(self) -> None:
        self.register_match("hobby-museum-city")

    @_register_rule(
        name="family-relax-tour",
        priority=260,
        recommendation=(
            "Рекомендуется спокойный семейный отдых с понятной логистикой и "
            "инфраструктурой для взрослых и детей."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="family"),
            ConditionSpec(slot="travel_type", op="eq", value="relax"),
        ),
    )
    @Rule(TravelInput(companions="family", travel_type="relax"))
    def rule_family_relax_tour(self) -> None:
        self.register_match("family-relax-tour")

    @_register_rule(
        name="friends-active-tour",
        priority=259,
        recommendation=(
            "Рекомендуется активная поездка для друзей: спорт, прогулки и "
            "общая насыщенная программа."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="friends"),
            ConditionSpec(slot="travel_type", op="eq", value="active"),
        ),
    )
    @Rule(TravelInput(companions="friends", travel_type="active"))
    def rule_friends_active_tour(self) -> None:
        self.register_match("friends-active-tour")

    @_register_rule(
        name="business-general",
        priority=250,
        recommendation=(
            "Рекомендуется деловой формат поездки с проживанием в удобной "
            "локации и запасом времени под встречи."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="business"),
        ),
    )
    @Rule(TravelInput(travel_type="business"))
    def rule_business_general(self) -> None:
        self.register_match("business-general")

    @_register_rule(
        name="eco-general",
        priority=249,
        recommendation=(
            "Рекомендуется экологический тур с природными локациями и "
            "бережным режимом посещения."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="eco"),
        ),
    )
    @Rule(TravelInput(travel_type="eco"))
    def rule_eco_general(self) -> None:
        self.register_match("eco-general")

    @_register_rule(
        name="education-general",
        priority=248,
        recommendation=(
            "Рекомендуется обучающий тур с курсами, мастер-классами или "
            "тематической программой."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="education"),
        ),
    )
    @Rule(TravelInput(travel_type="education"))
    def rule_education_general(self) -> None:
        self.register_match("education-general")

    @_register_rule(
        name="health-general",
        priority=247,
        recommendation=(
            "Рекомендуется оздоровительный отдых с размеренным темпом и "
            "восстановительными процедурами."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="health"),
        ),
    )
    @Rule(TravelInput(travel_type="health"))
    def rule_health_general(self) -> None:
        self.register_match("health-general")

    @_register_rule(
        name="culture-general",
        priority=246,
        recommendation=(
            "Рекомендуется культурно-познавательная поездка с экскурсиями и "
            "городской программой."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="culture"),
        ),
    )
    @Rule(TravelInput(travel_type="culture"))
    def rule_culture_general(self) -> None:
        self.register_match("culture-general")

    @_register_rule(
        name="relax-general",
        priority=245,
        recommendation=(
            "Рекомендуется спокойный отдых с комфортным размещением и "
            "минимумом перегрузки в программе."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="relax"),
        ),
    )
    @Rule(TravelInput(travel_type="relax"))
    def rule_relax_general(self) -> None:
        self.register_match("relax-general")

    @_register_rule(
        name="active-general",
        priority=244,
        recommendation=(
            "Рекомендуется активный формат поездки с походами, спортом или "
            "движением по нескольким точкам маршрута."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="active"),
        ),
    )
    @Rule(TravelInput(travel_type="active"))
    def rule_active_general(self) -> None:
        self.register_match("active-general")

    @_register_rule(
        name="mixed-general",
        priority=243,
        recommendation=(
            "Рекомендуется смешанный формат путешествия: баланс отдыха, "
            "экскурсий и умеренной активности."
        ),
        conditions=(
            ConditionSpec(slot="travel_type", op="eq", value="mixed"),
        ),
    )
    @Rule(TravelInput(travel_type="mixed"))
    def rule_mixed_general(self) -> None:
        self.register_match("mixed-general")

    @Rule(TravelInput(), salience=-1000)
    def rule_default(self) -> None:
        if self.selected_rule is None:
            self.register_match(DEFAULT_RULE_NAME)


class TravelRuleEngine:
    """Rule engine based on experta with forward and backward explain output."""

    def __init__(self) -> None:
        self.engine = _TravelExpertEngine()
        self.fact_types = {
            spec.fact_slot: spec.field_type
            for spec in TRAVEL_FACTS
            if spec.fact_slot is not None
        }

    def rules_count(self) -> int:
        return len(self.engine.rule_metadata) - 1

    def evaluate(
        self,
        facts: Mapping[str, Any],
        *,
        explain: bool = False,
    ) -> str | EvaluationResult:
        started = perf_counter()

        normalized = self._normalize_facts(facts)
        self.engine.reset_runtime_state()
        self.engine.reset()
        self.engine.declare(TravelInput(**normalized))
        self.engine.run()

        elapsed_ms = (perf_counter() - started) * 1000
        selected_rule = self.engine.selected_rule or DEFAULT_RULE_NAME

        if explain:
            return EvaluationResult(
                recommendation=self.engine.recommendation,
                matched_rules=tuple(self.engine.matched_rules),
                selected_rule=selected_rule,
                elapsed_ms=round(elapsed_ms, 3),
                passes=3,
                steps=self._build_forward_steps(
                    normalized=normalized,
                    matched_rules=tuple(self.engine.matched_rules),
                    selected_rule=selected_rule,
                ),
            )

        return self.engine.recommendation

    def backward(
        self,
        *,
        goal: str,
        known_facts: Mapping[str, Any],
        explain: bool = True,
    ) -> bool | BackwardResult:
        started = perf_counter()
        normalized = self._normalize_facts(known_facts)
        metadata = self.engine.rule_metadata
        steps: list[dict[str, Any]] = []
        self._append_backward_step(steps, depth=0, step="prove-goal", goal=goal)
        matched_rules: list[str] = []

        if goal == "*":
            candidates = _sorted_rules(metadata)
            self._append_backward_step(
                steps,
                depth=0,
                step="select-rules",
                goal=goal,
                candidates=[item.name for item in candidates],
            )
        else:
            candidate = metadata.get(goal)
            if candidate is None:
                self._append_backward_step(
                    steps,
                    depth=0,
                    step="goal-not-found",
                    goal=goal,
                )
                elapsed_ms = (perf_counter() - started) * 1000
                result = BackwardResult(
                    goal=goal,
                    achieved=False,
                    selected_rule=None,
                    matched_rules=(),
                    recommendation=None,
                    elapsed_ms=round(elapsed_ms, 3),
                    passes=max(step["pass"] for step in steps),
                    steps=tuple(steps),
                    proof={
                        "type": "goal",
                        "goal": goal,
                        "achieved": False,
                        "reason": "goal-not-found",
                    },
                )
                if explain:
                    return result
                return False
            candidates = [candidate]
            self._append_backward_step(
                steps,
                depth=0,
                step="select-rules",
                goal=goal,
                candidates=[candidate.name],
            )

        selected: RuleMetadata | None = None
        candidate_proofs: list[dict[str, Any]] = []

        for candidate in candidates:
            achieved_candidate, candidate_proof = self._build_backward_rule_proof(
                candidate=candidate,
                known_facts=normalized,
                steps=steps,
                depth=1,
            )
            candidate_proofs.append(candidate_proof)
            if achieved_candidate:
                matched_rules.append(candidate.name)
                if selected is None:
                    selected = candidate
                    self._append_backward_step(
                        steps,
                        depth=0,
                        step="goal-proved",
                        goal=goal,
                        selected_rule=candidate.name,
                    )
                    if goal != "*":
                        break
                else:
                    self._append_backward_step(
                        steps,
                        depth=0,
                        step="candidate-also-matched",
                        goal=goal,
                        rule=candidate.name,
                        selected_rule=selected.name,
                    )

        achieved = selected is not None
        if selected is None and goal in {"*", DEFAULT_RULE_NAME}:
            selected = metadata[DEFAULT_RULE_NAME]
            achieved = True
            matched_rules.append(DEFAULT_RULE_NAME)
            self._append_backward_step(
                steps,
                depth=0,
                step="fallback-default",
                goal=goal,
                rule=DEFAULT_RULE_NAME,
            )

        if not achieved and goal not in {"*", DEFAULT_RULE_NAME}:
            self._append_backward_step(
                steps,
                depth=0,
                step="goal-failed",
                goal=goal,
            )

        elapsed_ms = (perf_counter() - started) * 1000
        result = BackwardResult(
            goal=goal,
            achieved=achieved,
            selected_rule=selected.name if selected else None,
            matched_rules=tuple(matched_rules),
            recommendation=selected.recommendation if selected else None,
            elapsed_ms=round(elapsed_ms, 3),
            passes=max(step["pass"] for step in steps),
            steps=tuple(steps),
            proof={
                "type": "goal",
                "goal": goal,
                "achieved": achieved,
                "selected_rule": selected.name if selected else None,
                "matched_rules": list(matched_rules),
                "candidates": candidate_proofs,
            },
        )

        if explain:
            return result

        return achieved

    def _append_backward_step(
        self,
        steps: list[dict[str, Any]],
        *,
        depth: int,
        step: str,
        **payload: Any,
    ) -> None:
        steps.append(
            {
                "pass": depth + 1,
                "depth": depth,
                "step": step,
                **payload,
            }
        )

    def _build_backward_rule_proof(
        self,
        *,
        candidate: RuleMetadata,
        known_facts: Mapping[str, Any],
        steps: list[dict[str, Any]],
        depth: int,
    ) -> tuple[bool, dict[str, Any]]:
        self._append_backward_step(
            steps,
            depth=depth,
            step="try-rule",
            rule=candidate.name,
            priority=candidate.priority,
        )

        condition_proofs: list[dict[str, Any]] = []
        candidate_ok = True
        for condition in candidate.conditions:
            condition_ok, condition_proof = self._build_backward_condition_proof(
                condition=condition,
                known_facts=known_facts,
                steps=steps,
                depth=depth + 1,
                rule_name=candidate.name,
            )
            condition_proofs.append(condition_proof)
            if not condition_ok:
                candidate_ok = False

        self._append_backward_step(
            steps,
            depth=depth,
            step="rule-proved" if candidate_ok else "rule-failed",
            rule=candidate.name,
        )
        return (
            candidate_ok,
            {
                "type": "rule",
                "rule": candidate.name,
                "priority": candidate.priority,
                "achieved": candidate_ok,
                "conditions": condition_proofs,
            },
        )

    def _build_backward_condition_proof(
        self,
        *,
        condition: ConditionSpec,
        known_facts: Mapping[str, Any],
        steps: list[dict[str, Any]],
        depth: int,
        rule_name: str,
    ) -> tuple[bool, dict[str, Any]]:
        self._append_backward_step(
            steps,
            depth=depth,
            step="prove-condition",
            rule=rule_name,
            slot=condition.slot,
            operator=condition.op,
            expected=condition.value,
        )

        actual = known_facts.get(condition.slot)
        if actual is None:
            self._append_backward_step(
                steps,
                depth=depth,
                step="condition-failed",
                rule=rule_name,
                slot=condition.slot,
                operator=condition.op,
                expected=condition.value,
                actual=None,
                reason="missing-fact",
            )
            return (
                False,
                {
                    "type": "condition",
                    "rule": rule_name,
                    "slot": condition.slot,
                    "operator": condition.op,
                    "expected": condition.value,
                    "actual": None,
                    "achieved": False,
                    "source": "facts",
                    "reason": "missing-fact",
                },
            )

        condition_ok = _apply_operator(condition.op, actual, condition.value)
        self._append_backward_step(
            steps,
            depth=depth,
            step="condition-from-facts" if condition_ok else "condition-failed",
            rule=rule_name,
            slot=condition.slot,
            operator=condition.op,
            expected=condition.value,
            actual=actual,
            matched=condition_ok,
        )
        return (
            condition_ok,
            {
                "type": "condition",
                "rule": rule_name,
                "slot": condition.slot,
                "operator": condition.op,
                "expected": condition.value,
                "actual": actual,
                "achieved": condition_ok,
                "source": "facts",
            },
        )

    def _build_forward_steps(
        self,
        *,
        normalized: Mapping[str, Any],
        matched_rules: tuple[str, ...],
        selected_rule: str,
    ) -> tuple[dict[str, Any], ...]:
        steps: list[dict[str, Any]] = [
            {
                "pass": 1,
                "step": "declare-facts",
                "facts": dict(normalized),
            },
            {
                "pass": 2,
                "step": "select-candidates",
                "candidates": [item.name for item in _sorted_rules(self.engine.rule_metadata)],
            },
        ]
        matched_set = set(matched_rules)

        for candidate in _sorted_rules(self.engine.rule_metadata):
            candidate_ok = True
            for condition in candidate.conditions:
                condition_ok = _condition_is_satisfied(condition, normalized)
                steps.append(
                    {
                        "pass": 2,
                        "step": "check-condition",
                        "rule": candidate.name,
                        "slot": condition.slot,
                        "operator": condition.op,
                        "expected": condition.value,
                        "actual": normalized.get(condition.slot),
                        "matched": condition_ok,
                    }
                )
                if not condition_ok:
                    candidate_ok = False

            if candidate_ok:
                steps.append(
                    {
                        "pass": 2,
                        "step": "rule-matched",
                        "rule": candidate.name,
                        "fired": candidate.name in matched_set,
                        "selected": candidate.name == selected_rule,
                    }
                )

        if selected_rule == DEFAULT_RULE_NAME:
            steps.append(
                {
                    "pass": 3,
                    "step": "fallback-default",
                    "rule": DEFAULT_RULE_NAME,
                }
            )
        else:
            steps.append(
                {
                    "pass": 3,
                    "step": "select-rule",
                    "rule": selected_rule,
                    "matched_rules": list(matched_rules),
                }
            )

        return tuple(steps)

    def _normalize_facts(self, raw_facts: Mapping[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for slot, field_type in self.fact_types.items():
            value = raw_facts.get(slot)
            if value is None or value == "":
                continue
            if field_type == "integer":
                normalized[slot] = int(value)
            else:
                normalized[slot] = value
        return normalized


def init_rule_engine(app: "Flask") -> TravelRuleEngine:
    engine = TravelRuleEngine()
    app.extensions["expert_engine"] = engine
    return engine
