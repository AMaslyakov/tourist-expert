from __future__ import annotations

import unittest

from app.rules import EvaluationResult, TravelRuleEngine


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


if __name__ == "__main__":
    unittest.main()
