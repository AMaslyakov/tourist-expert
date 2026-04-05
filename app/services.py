from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from flask_wtf import FlaskForm

from app.forms import get_evaluation_input, get_session_input
from app.rules import (
    DEFAULT_RULE_NAME,
    BackwardResult,
    EvaluationResult,
    TravelRuleEngine,
)

SAMPLE_TEST_FACTS: dict[str, object] = {
    "season": "summer",
    "hobby": "dance",
    "budget_rub": 150000,
    "trip_days": 10,
    "climate": "warm",
    "travel_type": "relax",
    "companions": "couple",
    "service_level": "premium",
    "visa_mode": "visa_ready",
    "insurance": "yes",
}


@dataclass(frozen=True)
class ConsultationOutcome:
    recommendation_text: str | None
    session_payload: dict[str, Any] | None


def build_consultation_outcome(form: FlaskForm, engine: object) -> ConsultationOutcome:
    if not isinstance(engine, TravelRuleEngine):
        return ConsultationOutcome(recommendation_text=None, session_payload=None)

    evaluation_input = get_evaluation_input(form)
    evaluation_result = engine.evaluate(evaluation_input, explain=True)
    if not isinstance(evaluation_result, EvaluationResult):
        return ConsultationOutcome(recommendation_text=None, session_payload=None)

    backward_result = engine.backward(
        goal="*",
        known_facts=evaluation_input,
        explain=True,
    )
    if not isinstance(backward_result, BackwardResult):
        return ConsultationOutcome(
            recommendation_text=evaluation_result.recommendation,
            session_payload=None,
        )

    session_payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": get_session_input(form),
        "recommendation": evaluation_result.recommendation,
        "explain": {
            "forward": _build_forward_explain(evaluation_result),
            "backward": _build_backward_explain(backward_result),
        },
    }
    return ConsultationOutcome(
        recommendation_text=evaluation_result.recommendation,
        session_payload=session_payload,
    )


def build_test_route_context(engine: object, run_tests: bool) -> dict[str, Any]:
    if not isinstance(engine, TravelRuleEngine):
        return {
            "engine_error": True,
            "run_tests": run_tests,
            "default_rule_name": DEFAULT_RULE_NAME,
        }

    sample_facts = dict(SAMPLE_TEST_FACTS)
    forward_result: EvaluationResult | None = None
    backward_result: BackwardResult | None = None
    backward_steps: tuple[dict[str, object], ...] = ()
    rule_chains: list[dict[str, object]] = []

    if run_tests:
        maybe_forward = engine.evaluate(sample_facts, explain=True)
        if isinstance(maybe_forward, EvaluationResult):
            forward_result = maybe_forward

        maybe_backward = engine.backward(
            goal="*",
            known_facts=sample_facts,
            explain=True,
        )
        if isinstance(maybe_backward, BackwardResult):
            backward_result = maybe_backward
            backward_steps = maybe_backward.steps
            rule_chains = _extract_rule_chains(maybe_backward.proof)

    all_rules = sorted(
        (
            metadata
            for metadata in engine.engine.rule_metadata.values()
            if metadata.name != DEFAULT_RULE_NAME
        ),
        key=lambda metadata: metadata.priority,
        reverse=True,
    )

    return {
        "engine_error": False,
        "run_tests": run_tests,
        "sample_facts": sample_facts,
        "rules_count": engine.rules_count(),
        "all_rules": all_rules,
        "forward_result": forward_result,
        "backward_result": backward_result,
        "backward_steps": backward_steps,
        "rule_chains": rule_chains,
        "default_rule_name": DEFAULT_RULE_NAME,
    }


def _build_forward_explain(evaluation_result: EvaluationResult) -> dict[str, object]:
    return {
        "matched_rules": list(evaluation_result.matched_rules),
        "selected_rule": evaluation_result.selected_rule,
        "elapsed_ms": evaluation_result.elapsed_ms,
        "passes": evaluation_result.passes,
        "steps": list(evaluation_result.steps),
    }


def _build_backward_explain(backward_result: BackwardResult) -> dict[str, object]:
    return {
        "goal": backward_result.goal,
        "achieved": backward_result.achieved,
        "selected_rule": backward_result.selected_rule,
        "matched_rules": list(backward_result.matched_rules),
        "recommendation": backward_result.recommendation,
        "elapsed_ms": backward_result.elapsed_ms,
        "passes": backward_result.passes,
        "steps": list(backward_result.steps),
        "proof": backward_result.proof,
    }


def _extract_rule_chains(proof: dict[str, Any] | None) -> list[dict[str, object]]:
    if not isinstance(proof, dict):
        return []

    raw_candidates = proof.get("candidates")
    if not isinstance(raw_candidates, list):
        return []

    return [item for item in raw_candidates if isinstance(item, dict)]
