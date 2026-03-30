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


@dataclass(frozen=True)
class BackwardResult:
    goal: str
    achieved: bool
    selected_rule: str | None
    recommendation: str | None
    elapsed_ms: float
    passes: int
    steps: tuple[dict[str, Any], ...]


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
        priority=300,
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
        salience=300,
    )
    def rule_warm_relax_premium(self, budget: int) -> None:  # noqa: ARG002
        self.register_match("warm-relax-premium")

    @_register_rule(
        name="hobby-dance-korea",
        priority=280,
        recommendation="Рекомендуется поездка в Южную Корею.",
        conditions=(
            ConditionSpec(slot="hobby", op="eq", value="dance"),
        ),
    )
    @Rule(TravelInput(hobby="dance"), salience=280)
    def rule_hobby_dance_korea(self) -> None:
        self.register_match("hobby-dance-korea")

    @_register_rule(
        name="active-short-budget",
        priority=250,
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
        salience=250,
    )
    def rule_active_short_budget(self, budget: int, days: int) -> None:  # noqa: ARG002
        self.register_match("active-short-budget")

    @_register_rule(
        name="family-mild-climate",
        priority=220,
        recommendation=(
            "Рекомендуется семейный отдых в умеренном климате с короткими "
            "переездами."
        ),
        conditions=(
            ConditionSpec(slot="companions", op="eq", value="family"),
            ConditionSpec(slot="climate", op="eq", value="mild"),
        ),
    )
    @Rule(TravelInput(companions="family", climate="mild"), salience=220)
    def rule_family_mild_climate(self) -> None:
        self.register_match("family-mild-climate")

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
        return len(self.engine.rule_metadata)

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
                passes=2,
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

        if goal == "*":
            candidates = sorted(
                (
                    item
                    for item in metadata.values()
                    if item.name != DEFAULT_RULE_NAME
                ),
                key=lambda item: item.priority,
                reverse=True,
            )
            steps.append(
                {
                    "pass": 1,
                    "step": "select-candidates",
                    "goal": goal,
                    "candidates": [item.name for item in candidates],
                }
            )
        else:
            candidate = metadata.get(goal)
            if candidate is None:
                elapsed_ms = (perf_counter() - started) * 1000
                result = BackwardResult(
                    goal=goal,
                    achieved=False,
                    selected_rule=None,
                    recommendation=None,
                    elapsed_ms=round(elapsed_ms, 3),
                    passes=1,
                    steps=(
                        {
                            "pass": 1,
                            "step": "goal-not-found",
                            "goal": goal,
                        },
                    ),
                )
                if explain:
                    return result
                return False

            candidates = [candidate]
            steps.append(
                {
                    "pass": 1,
                    "step": "select-goal",
                    "goal": goal,
                    "candidate": candidate.name,
                }
            )

        selected: RuleMetadata | None = None
        for candidate in candidates:
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
                selected = candidate
                steps.append(
                    {
                        "pass": 2,
                        "step": "goal-achieved",
                        "rule": candidate.name,
                    }
                )
                break

        achieved = selected is not None
        if selected is None and goal in {"*", DEFAULT_RULE_NAME}:
            selected = metadata[DEFAULT_RULE_NAME]
            achieved = True
            steps.append(
                {
                    "pass": 2,
                    "step": "fallback-default",
                    "rule": DEFAULT_RULE_NAME,
                }
            )

        elapsed_ms = (perf_counter() - started) * 1000
        result = BackwardResult(
            goal=goal,
            achieved=achieved,
            selected_rule=selected.name if selected else None,
            recommendation=selected.recommendation if selected else None,
            elapsed_ms=round(elapsed_ms, 3),
            passes=2,
            steps=tuple(steps),
        )

        if explain:
            return result

        return achieved

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
