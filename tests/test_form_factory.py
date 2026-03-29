from __future__ import annotations

import unittest

from flask import Flask
from werkzeug.datastructures import MultiDict

from app.knowledge import TRAVEL_FACTS
from app.forms import LandingForm, SUBMIT_FIELD_NAME, VISIBLE_FORM_FIELDS, get_evaluation_input


class FormFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.flask_app = Flask(__name__)
        self.flask_app.config["SECRET_KEY"] = "test-secret"
        self.flask_app.config["WTF_CSRF_ENABLED"] = False
        self.app_context = self.flask_app.app_context()
        self.app_context.push()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_visible_fields_follow_schema_order(self) -> None:
        expected = [
            spec.name for spec in TRAVEL_FACTS if spec.field_type != "submit"
        ]
        actual = [spec.name for spec in VISIBLE_FORM_FIELDS]
        self.assertEqual(actual, expected)
        self.assertEqual(SUBMIT_FIELD_NAME, "submit")

    def test_build_fact_payload_from_form_data(self) -> None:
        form = LandingForm(
            formdata=MultiDict(
                {
                    "departure_city": "Екатеринбург",
                    "hobby": "dance",
                    "budget_rub": "120000",
                    "trip_days": "10",
                    "climate": "warm",
                    "travel_type": "relax",
                    "companions": "couple",
                    "notes": "Только прямые рейсы",
                    "submit": "1",
                }
            )
        )

        self.assertTrue(form.validate())
        payload = get_evaluation_input(form)

        self.assertEqual(
            payload,
            {
                "budget_rub": 120000,
                "trip_days": 10,
                "climate": "warm",
                "travel_type": "relax",
                "companions": "couple",
                "hobby": "dance",
            },
        )


if __name__ == "__main__":
    unittest.main()
