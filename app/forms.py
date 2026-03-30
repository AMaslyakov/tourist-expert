from __future__ import annotations

from flask_wtf import FlaskForm

from app.form_factory import build_fact_payload, build_form_class, build_session_payload
from app.knowledge import TRAVEL_FACTS

LandingForm = build_form_class("LandingForm", TRAVEL_FACTS)

VISIBLE_FORM_FIELDS = tuple(spec for spec in TRAVEL_FACTS if spec.field_type != "submit")
SUBMIT_FIELD_NAME = next(
    spec.name for spec in TRAVEL_FACTS if spec.field_type == "submit"
)


def get_evaluation_input(form: FlaskForm) -> dict[str, object]:
    return build_fact_payload(form, TRAVEL_FACTS)


def get_session_input(form: FlaskForm) -> dict[str, object]:
    return build_session_payload(form, TRAVEL_FACTS)
