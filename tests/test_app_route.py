from __future__ import annotations

import unittest
from unittest.mock import patch

from app import create_app


class AppRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_index_get_returns_page(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Консультант по путешествиям", response.get_data(as_text=True))

    def test_index_post_builds_recommendation_and_saves_session(self) -> None:
        post_data = {
            "departure_city": "Екатеринбург",
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

        with patch("app.save_consultation_session") as save_mock:
            response = self.client.post("/", data=post_data)

        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Рекомендация системы", html)
        self.assertIn("пляжный отдых", html)
        save_mock.assert_called_once()
        saved_payload = save_mock.call_args.args[0]
        self.assertIn("explain", saved_payload)
        self.assertIn("forward", saved_payload["explain"])
        self.assertIn("backward", saved_payload["explain"])
        self.assertIn("steps", saved_payload["explain"]["forward"])
        self.assertIn("matched_rules", saved_payload["explain"]["backward"])
        self.assertIn("proof", saved_payload["explain"]["backward"])
        self.assertEqual(
            saved_payload["explain"]["forward"]["selected_rule"],
            "warm-relax-premium",
        )
        self.assertEqual(saved_payload["explain"]["backward"]["goal"], "*")
        self.assertEqual(
            saved_payload["explain"]["backward"]["selected_rule"],
            "warm-relax-premium",
        )

    def test_test_route_returns_forward_and_backward_matches(self) -> None:
        response = self.client.get("/test")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Тестовый запуск продукционной системы", html)
        self.assertIn("Запустить тесты", html)
        self.assertIn("Ожидание запуска", html)

    def test_test_route_run_tests_shows_rule_chains(self) -> None:
        response = self.client.get("/test?run_tests=1")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Прямой вывод", html)
        self.assertIn("Обратный вывод", html)
        self.assertIn("Цепочка шагов обратного вывода", html)
        self.assertIn("Цепочки для правил", html)
        self.assertIn("Все зарегистрированные правила", html)
        self.assertIn("warm-relax-premium", html)


if __name__ == "__main__":
    unittest.main()
