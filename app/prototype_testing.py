from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.knowledge import TRAVEL_FACTS
from app.rules import DEFAULT_RULE_NAME, BackwardResult, EvaluationResult, TravelRuleEngine

MIN_TRACE_STEPS = 51
MIN_TRACE_PASSES = 2

OPERATOR_LABELS = {
    "eq": "=",
    "lt": "<",
    "lte": "<=",
    "gt": ">",
    "gte": ">=",
}

FORWARD_PASS_EXPLANATION = (
    "1-й проход: загрузка исходных фактов. "
    "2-й проход: последовательная проверка правил и формирование конфликтного множества. "
    "3-й проход: разрешение конфликта и выбор итоговой рекомендации."
)

BACKWARD_PASS_EXPLANATION = (
    "1-й проход: постановка цели и подбор правил-кандидатов. "
    "2-й проход: попытка доказать каждое правило. "
    "3-й проход: доказательство подцелей по исходным фактам."
)


@dataclass(frozen=True)
class PrototypeScenario:
    slug: str
    title: str
    summary: str
    facts: dict[str, Any]
    backward_goal: str
    backward_goal_label: str


FACT_LABELS = {
    spec.fact_slot: spec.label
    for spec in TRAVEL_FACTS
    if spec.fact_slot is not None
}

FACT_CHOICE_LABELS = {
    spec.fact_slot: dict(spec.choices)
    for spec in TRAVEL_FACTS
    if spec.fact_slot is not None
}

PROTOTYPE_SCENARIOS: tuple[PrototypeScenario, ...] = (
    PrototypeScenario(
        slug="premium-relax",
        title="Пример 1. Летний премиальный отдых для пары",
        summary=(
            "Сценарий показывает конфликт нескольких подходящих правил и выбор "
            "самой приоритетной пляжной рекомендации."
        ),
        facts={
            "season": "summer",
            "hobby": "museum",
            "budget_rub": 150000,
            "trip_days": 10,
            "climate": "warm",
            "travel_type": "relax",
            "companions": "couple",
            "service_level": "premium",
            "visa_mode": "visa_ready",
            "insurance": "yes",
        },
        backward_goal="*",
        backward_goal_label=(
            "Определить, какая рекомендация из базы знаний должна быть доказана "
            "для данного набора фактов (`*`)."
        ),
    ),
    PrototypeScenario(
        slug="winter-active",
        title="Пример 2. Зимний активный тур для компании друзей",
        summary=(
            "Сценарий показывает выбор активной зимней рекомендации на фоне "
            "нескольких конкурирующих правил."
        ),
        facts={
            "season": "winter",
            "hobby": "hiking",
            "budget_rub": 120000,
            "trip_days": 8,
            "climate": "cold",
            "travel_type": "active",
            "companions": "friends",
            "service_level": "standard",
            "visa_mode": "visa_ready",
            "insurance": "yes",
        },
        backward_goal="*",
        backward_goal_label=(
            "Определить, какая рекомендация из базы знаний должна быть доказана "
            "для зимнего активного сценария (`*`)."
        ),
    ),
)


def get_prototype_scenario_previews() -> list[dict[str, str]]:
    return [
        {
            "title": scenario.title,
            "summary": scenario.summary,
            "backward_goal_label": scenario.backward_goal_label,
        }
        for scenario in PROTOTYPE_SCENARIOS
    ]


def build_prototype_testing_context(engine: TravelRuleEngine) -> dict[str, Any]:
    scenario_cards: list[dict[str, Any]] = []
    for scenario in PROTOTYPE_SCENARIOS:
        forward_result = engine.evaluate(scenario.facts, explain=True)
        backward_result = engine.backward(
            goal=scenario.backward_goal,
            known_facts=scenario.facts,
            explain=True,
        )
        scenario_cards.append(
            _build_scenario_card(
                engine=engine,
                scenario=scenario,
                forward_result=forward_result,
                backward_result=backward_result,
            )
        )

    return {
        "scenarios": scenario_cards,
        "thresholds": {
            "steps": MIN_TRACE_STEPS,
            "passes": MIN_TRACE_PASSES,
        },
        "forward_pass_explanation": FORWARD_PASS_EXPLANATION,
        "backward_pass_explanation": BACKWARD_PASS_EXPLANATION,
        "performance": _build_performance_summary(scenario_cards),
    }


def _build_scenario_card(
    *,
    engine: TravelRuleEngine,
    scenario: PrototypeScenario,
    forward_result: EvaluationResult,
    backward_result: BackwardResult,
) -> dict[str, Any]:
    return {
        "slug": scenario.slug,
        "title": scenario.title,
        "summary": scenario.summary,
        "facts": _build_fact_rows(scenario.facts),
        "forward": _build_forward_card(engine, forward_result),
        "backward": _build_backward_card(
            engine=engine,
            scenario=scenario,
            result=backward_result,
        ),
    }


def _build_forward_card(
    engine: TravelRuleEngine,
    result: EvaluationResult,
) -> dict[str, Any]:
    return {
        "selected_rule": result.selected_rule,
        "recommendation": result.recommendation,
        "elapsed_ms": result.elapsed_ms,
        "passes": result.passes,
        "step_count": len(result.steps),
        "meets_step_requirement": len(result.steps) >= MIN_TRACE_STEPS,
        "meets_pass_requirement": result.passes >= MIN_TRACE_PASSES,
        "selected_priority": engine.engine.rule_metadata[result.selected_rule].priority,
        "matched_rules": _build_rule_rows(engine, result.matched_rules),
        "trace_steps": [
            {
                "pass": step["pass"],
                "code": step["step"],
                "message": _describe_forward_step(step),
            }
            for step in result.steps
        ],
    }


def _build_backward_card(
    *,
    engine: TravelRuleEngine,
    scenario: PrototypeScenario,
    result: BackwardResult,
) -> dict[str, Any]:
    selected_priority = None
    if result.selected_rule is not None:
        selected_priority = engine.engine.rule_metadata[result.selected_rule].priority

    return {
        "goal": result.goal,
        "goal_label": scenario.backward_goal_label,
        "achieved": result.achieved,
        "selected_rule": result.selected_rule,
        "recommendation": result.recommendation,
        "elapsed_ms": result.elapsed_ms,
        "passes": result.passes,
        "step_count": len(result.steps),
        "meets_step_requirement": len(result.steps) >= MIN_TRACE_STEPS,
        "meets_pass_requirement": result.passes >= MIN_TRACE_PASSES,
        "selected_priority": selected_priority,
        "matched_rules": _build_rule_rows(engine, result.matched_rules),
        "trace_steps": [
            {
                "pass": step["pass"],
                "depth": step.get("depth", 0),
                "code": step["step"],
                "message": _describe_backward_step(step),
            }
            for step in result.steps
        ],
    }


def _build_performance_summary(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    forward_total = 0.0
    backward_total = 0.0

    for scenario in scenarios:
        forward_ms = scenario["forward"]["elapsed_ms"]
        backward_ms = scenario["backward"]["elapsed_ms"]
        forward_total += forward_ms
        backward_total += backward_ms

        delta_ms = round(forward_ms - backward_ms, 3)
        if delta_ms > 0:
            faster = "Обратный вывод"
        elif delta_ms < 0:
            faster = "Прямой вывод"
        else:
            faster = "Одинаково"

        rows.append(
            {
                "title": scenario["title"],
                "forward_ms": forward_ms,
                "backward_ms": backward_ms,
                "delta_ms": abs(delta_ms),
                "faster": faster,
            }
        )

    count = len(scenarios) or 1
    average_forward = round(forward_total / count, 3)
    average_backward = round(backward_total / count, 3)
    difference = round(abs(average_forward - average_backward), 3)

    if average_forward > average_backward:
        comparison = (
            "В текущей реализации среднее время обратного вывода меньше. "
            "Это ожидаемо: прямой вывод реально запускает движок `experta`, "
            "а обратный вывод строит доказательство по метаданным правил."
        )
    elif average_forward < average_backward:
        comparison = (
            "В текущей реализации среднее время прямого вывода меньше. "
            "Обратный вывод тратит больше времени на пошаговое доказательство цели."
        )
    else:
        comparison = (
            "Среднее время прямого и обратного вывода практически совпало "
            "на двух демонстрационных сценариях."
        )

    return {
        "rows": rows,
        "average_forward_ms": average_forward,
        "average_backward_ms": average_backward,
        "average_difference_ms": difference,
        "comparison": comparison,
    }


def _build_fact_rows(facts: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "slot": slot,
            "label": FACT_LABELS.get(slot, slot),
            "value": _format_fact_value(slot, value),
            "raw_value": value,
        }
        for slot, value in facts.items()
    ]


def _build_rule_rows(
    engine: TravelRuleEngine,
    rules: tuple[str, ...] | list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule_name in rules:
        metadata = engine.engine.rule_metadata[rule_name]
        rows.append(
            {
                "name": metadata.name,
                "priority": metadata.priority,
                "recommendation": metadata.recommendation,
                "is_default": metadata.name == DEFAULT_RULE_NAME,
            }
        )
    return rows


def _describe_forward_step(step: Mapping[str, Any]) -> str:
    step_code = step["step"]
    if step_code == "declare-facts":
        facts = step["facts"]
        facts_text = "; ".join(
            f"{FACT_LABELS.get(slot, slot)} = {_format_fact_value(slot, value)}"
            for slot, value in facts.items()
        )
        return f"В систему загружены исходные факты: {facts_text}."

    if step_code == "select-candidates":
        return (
            f"Сформирован упорядоченный список из {len(step['candidates'])} правил "
            "для полного прохода по базе знаний."
        )

    if step_code == "inspect-rule":
        return (
            f"Начинаем проверку правила `{step['rule']}` "
            f"(priority={step['priority']})."
        )

    if step_code == "check-condition":
        operator = OPERATOR_LABELS[step["operator"]]
        return (
            f"Проверяем условие правила `{step['rule']}`: "
            f"{FACT_LABELS.get(step['slot'], step['slot'])} {operator} "
            f"{_format_fact_value(step['slot'], step['expected'])}; "
            f"фактическое значение {_format_fact_value(step['slot'], step['actual'])}. "
            f"Результат: {'выполнено' if step['matched'] else 'не выполнено'}."
        )

    if step_code == "rule-matched":
        return (
            f"Правило `{step['rule']}` подтверждено и добавлено в конфликтное множество."
        )

    if step_code == "rule-rejected":
        return (
            f"Правило `{step['rule']}` пропущено: хотя бы одно из его условий "
            "не подтвердилось."
        )

    if step_code == "resolve-conflict":
        return (
            f"Конфликтное множество сформировано: найдено {len(step['matched_rules'])} "
            "подходящих правил."
        )

    if step_code == "select-rule":
        return (
            f"По наивысшему приоритету выбрано правило `{step['rule']}` "
            "как итог прямого вывода."
        )

    if step_code == "fallback-default":
        return (
            "Подходящих правил не найдено, поэтому выбран вариант по умолчанию."
        )

    return f"Шаг прямого вывода `{step_code}`."


def _describe_backward_step(step: Mapping[str, Any]) -> str:
    step_code = step["step"]
    if step_code == "prove-goal":
        return f"Начинаем доказательство цели `{step['goal']}`."

    if step_code == "select-rules":
        return (
            f"Для цели `{step['goal']}` выбрано {len(step['candidates'])} "
            "правил-кандидатов."
        )

    if step_code == "try-rule":
        return (
            f"Пробуем доказать правило `{step['rule']}` "
            f"(priority={step['priority']})."
        )

    if step_code == "prove-condition":
        operator = OPERATOR_LABELS[step["operator"]]
        return (
            f"Формируем подцель для правила `{step['rule']}`: "
            f"{FACT_LABELS.get(step['slot'], step['slot'])} {operator} "
            f"{_format_fact_value(step['slot'], step['expected'])}."
        )

    if step_code == "condition-from-facts":
        operator = OPERATOR_LABELS[step["operator"]]
        return (
            f"Подцель подтверждена исходным фактом: "
            f"{FACT_LABELS.get(step['slot'], step['slot'])} {operator} "
            f"{_format_fact_value(step['slot'], step['expected'])}; "
            f"фактическое значение {_format_fact_value(step['slot'], step['actual'])}."
        )

    if step_code == "condition-failed":
        operator = OPERATOR_LABELS[step["operator"]]
        actual = step.get("actual")
        if actual is None:
            return (
                f"Подцель не доказана: отсутствует факт "
                f"`{step['slot']}`, необходимый для условия "
                f"{FACT_LABELS.get(step['slot'], step['slot'])} {operator} "
                f"{_format_fact_value(step['slot'], step['expected'])}."
            )
        return (
            f"Подцель не доказана: "
            f"{FACT_LABELS.get(step['slot'], step['slot'])} {operator} "
            f"{_format_fact_value(step['slot'], step['expected'])}, "
            f"но фактическое значение равно {_format_fact_value(step['slot'], actual)}."
        )

    if step_code == "rule-proved":
        return f"Все подцели правила `{step['rule']}` доказаны."

    if step_code == "rule-failed":
        return (
            f"Правило `{step['rule']}` не доказано, поэтому переходим "
            "к следующей гипотезе."
        )

    if step_code == "goal-proved":
        return (
            f"Цель `{step['goal']}` доказана. Выбрано правило "
            f"`{step['selected_rule']}`."
        )

    if step_code == "candidate-also-matched":
        return (
            f"Правило `{step['rule']}` тоже доказано, но итогом остаётся "
            f"`{step['selected_rule']}` из-за более высокого приоритета."
        )

    if step_code == "fallback-default":
        return (
            f"Обычные правила не доказаны, поэтому используется "
            f"правило `{step['rule']}`."
        )

    if step_code == "goal-failed":
        return f"Цель `{step['goal']}` не доказана."

    if step_code == "goal-not-found":
        return f"Цель `{step['goal']}` отсутствует в базе правил."

    return f"Шаг обратного вывода `{step_code}`."


def _format_fact_value(slot: str, value: Any) -> str:
    if value is None:
        return "не указано"

    choice_label = FACT_CHOICE_LABELS.get(slot, {}).get(value)
    if choice_label is not None:
        return f"{choice_label} [{value}]"

    return str(value)
