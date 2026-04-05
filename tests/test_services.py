from __future__ import annotations

import unittest

from app import create_app
from app.forms import LandingForm
from app.rules import DEFAULT_RULE_NAME
from app.services import build_consultation_outcome, build_test_route_context


class ServiceLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False

    def test_build_consultation_outcome_returns_payload(self) -> None:
        post_data = {
            "season": "summer",
            "hobby": "museum",
            "budget_rub": "130000",
            "trip_days": "10",
            "climate": "warm",
            "travel_type": "relax",
            "companions": "couple",
            "service_level": "premium",
            "visa_mode": "visa_ready",
            "insurance": "yes",
            "notes": "Без пересадок",
            "submit": "1",
        }
        with self.app.test_request_context("/", method="POST", data=post_data):
            form = LandingForm()
            engine = self.app.extensions["expert_engine"]
            outcome = build_consultation_outcome(form, engine)

        self.assertIsNotNone(outcome.recommendation_text)
        self.assertIsNotNone(outcome.session_payload)
        assert outcome.session_payload is not None
        self.assertIn("explain", outcome.session_payload)
        self.assertIn("forward", outcome.session_payload["explain"])
        self.assertIn("backward", outcome.session_payload["explain"])
        self.assertEqual(
            outcome.session_payload["explain"]["forward"]["selected_rule"],
            "warm-relax-premium",
        )
        self.assertEqual(outcome.session_payload["explain"]["backward"]["goal"], "*")

    def test_build_consultation_outcome_rejects_unknown_engine(self) -> None:
        with self.app.test_request_context("/", method="POST", data={"submit": "1"}):
            form = LandingForm()
            outcome = build_consultation_outcome(form, object())

        self.assertIsNone(outcome.recommendation_text)
        self.assertIsNone(outcome.session_payload)

    def test_build_test_route_context_without_run(self) -> None:
        engine = self.app.extensions["expert_engine"]
        context = build_test_route_context(engine, run_tests=False)

        self.assertFalse(context["engine_error"])
        self.assertFalse(context["run_tests"])
        self.assertIsNone(context["forward_result"])
        self.assertIsNone(context["backward_result"])
        self.assertEqual(context["rule_chains"], [])
        self.assertEqual(context["default_rule_name"], DEFAULT_RULE_NAME)

    def test_build_test_route_context_with_run(self) -> None:
        engine = self.app.extensions["expert_engine"]
        context = build_test_route_context(engine, run_tests=True)

        self.assertFalse(context["engine_error"])
        self.assertTrue(context["run_tests"])
        self.assertIsNotNone(context["forward_result"])
        self.assertIsNotNone(context["backward_result"])
        self.assertGreater(len(context["rule_chains"]), 0)

        forward_result = context["forward_result"]
        backward_result = context["backward_result"]
        assert forward_result is not None
        assert backward_result is not None
        self.assertEqual(forward_result.selected_rule, "warm-relax-premium")
        self.assertEqual(backward_result.goal, "*")

    def test_build_test_route_context_handles_engine_error(self) -> None:
        context = build_test_route_context(object(), run_tests=True)

        self.assertTrue(context["engine_error"])
        self.assertTrue(context["run_tests"])
        self.assertEqual(context["default_rule_name"], DEFAULT_RULE_NAME)


if __name__ == "__main__":
    unittest.main()
