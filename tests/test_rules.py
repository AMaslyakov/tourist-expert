from __future__ import annotations

import unittest

from app.rules import BackwardResult, EvaluationResult, TravelRuleEngine


class RuleEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = TravelRuleEngine()

    def test_rules_count_is_not_empty(self) -> None:
        self.assertGreaterEqual(self.engine.rules_count(), 4)

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
        self.assertIn("пляжный отдых", recommendation)

    def test_default_fallback_path(self) -> None:
        recommendation = self.engine.evaluate(
            {
                "climate": "cold",
                "travel_type": "culture",
                "companions": "solo",
                "budget_rub": 90000,
                "trip_days": 14,
                "hobby": "hiking",
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
                "hobby": "dance",
            },
            explain=True,
        )

        self.assertIsInstance(result, EvaluationResult)
        self.assertEqual(result.selected_rule, "warm-relax-premium")
        self.assertIn("hobby-dance-korea", result.matched_rules)

    def test_backward_goal_success(self) -> None:
        result = self.engine.backward(
            goal="warm-relax-premium",
            known_facts={
                "climate": "warm",
                "travel_type": "relax",
                "budget_rub": 140000,
            },
            explain=True,
        )

        self.assertIsInstance(result, BackwardResult)
        self.assertTrue(result.achieved)
        self.assertEqual(result.selected_rule, "warm-relax-premium")
        self.assertGreaterEqual(len(result.steps), 2)

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


if __name__ == "__main__":
    unittest.main()
