from __future__ import annotations

import unittest

from app.rules import BackwardResult, EvaluationResult, TravelRuleEngine


class RuleEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = TravelRuleEngine()

    def test_rules_count_is_not_empty(self) -> None:
        self.assertGreaterEqual(self.engine.rules_count(), 50)

    def test_premium_relax_path(self) -> None:
        recommendation = self.engine.evaluate(
            {
                "climate": "warm",
                "travel_type": "relax",
                "companions": "couple",
                "budget_rub": 150000,
                "trip_days": 10,
                "hobby": "museum",
            }
        )
        self.assertIn("пляжный отдых", recommendation.lower())

    def test_default_fallback_path(self) -> None:
        recommendation = self.engine.evaluate(
            {
                "climate": "cold",
                "budget_rub": 90000,
                "season": "winter",
            }
        )
        self.assertIn("универсальный экскурсионный отдых", recommendation)

    def test_explain_mode_returns_selected_rule(self) -> None:
        result = self.engine.evaluate(
            {
                "climate": "warm",
                "travel_type": "relax",
                "companions": "couple",
                "budget_rub": 130000,
                "trip_days": 9,
                "hobby": "museum",
            },
            explain=True,
        )

        self.assertIsInstance(result, EvaluationResult)
        self.assertEqual(result.selected_rule, "warm-relax-premium")
        self.assertIn("warm-relax-premium", result.matched_rules)
        self.assertGreater(len(result.steps), 50)

    def test_backward_goal_success(self) -> None:
        result = self.engine.backward(
            goal="*",
            known_facts={
                "season": "summer",
                "climate": "warm",
                "travel_type": "relax",
                "budget_rub": 140000,
                "service_level": "premium",
                "visa_mode": "visa_ready",
                "insurance": "yes",
            },
            explain=True,
        )

        self.assertIsInstance(result, BackwardResult)
        self.assertTrue(result.achieved)
        self.assertEqual(result.selected_rule, "warm-relax-premium")
        self.assertIn("warm-relax-premium", result.matched_rules)
        self.assertIsNotNone(result.proof)
        self.assertEqual(result.proof["type"], "goal")
        self.assertEqual(result.proof["goal"], "*")
        step_names = [step["step"] for step in result.steps]
        self.assertIn("prove-goal", step_names)
        self.assertIn("try-rule", step_names)
        self.assertIn("prove-condition", step_names)
        self.assertGreater(len(result.steps), 50)

    def test_backward_goal_not_found(self) -> None:
        result = self.engine.backward(
            goal="unknown-goal",
            known_facts={
                "climate": "warm",
                "travel_type": "relax",
                "budget_rub": 140000,
            },
            explain=True,
        )

        self.assertIsInstance(result, BackwardResult)
        self.assertFalse(result.achieved)
        self.assertIsNone(result.selected_rule)
        self.assertEqual(result.steps[-1]["step"], "goal-not-found")


if __name__ == "__main__":
    unittest.main()
