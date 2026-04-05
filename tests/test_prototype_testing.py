from __future__ import annotations

import unittest

from app.prototype_testing import build_prototype_testing_context
from app.rules import TravelRuleEngine


class PrototypeTestingContextTests(unittest.TestCase):
    def test_context_contains_two_scenarios_and_thresholds(self) -> None:
        context = build_prototype_testing_context(TravelRuleEngine())

        self.assertEqual(len(context["scenarios"]), 2)
        self.assertEqual(context["thresholds"]["steps"], 51)
        self.assertEqual(context["thresholds"]["passes"], 2)

        for scenario in context["scenarios"]:
            self.assertGreaterEqual(scenario["forward"]["step_count"], 51)
            self.assertGreaterEqual(scenario["forward"]["passes"], 2)
            self.assertTrue(scenario["forward"]["meets_step_requirement"])
            self.assertTrue(scenario["forward"]["meets_pass_requirement"])

            self.assertGreaterEqual(scenario["backward"]["step_count"], 51)
            self.assertGreaterEqual(scenario["backward"]["passes"], 2)
            self.assertTrue(scenario["backward"]["meets_step_requirement"])
            self.assertTrue(scenario["backward"]["meets_pass_requirement"])

        self.assertIn("average_forward_ms", context["performance"])
        self.assertIn("average_backward_ms", context["performance"])

    def test_context_keeps_expected_selected_rules(self) -> None:
        context = build_prototype_testing_context(TravelRuleEngine())

        selected_forward = {
            scenario["forward"]["selected_rule"]
            for scenario in context["scenarios"]
        }
        selected_backward = {
            scenario["backward"]["selected_rule"]
            for scenario in context["scenarios"]
        }

        self.assertEqual(
            selected_forward,
            {"warm-relax-premium", "winter-active-ski"},
        )
        self.assertEqual(selected_backward, selected_forward)


if __name__ == "__main__":
    unittest.main()
