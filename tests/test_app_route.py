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
            "hobby": "dance",
            "budget_rub": "130000",
            "trip_days": "10",
            "climate": "warm",
            "travel_type": "relax",
            "companions": "couple",
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


if __name__ == "__main__":
    unittest.main()
