from __future__ import annotations

from typing import Any

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange

from app.knowledge import FactSpec, ValidatorSpec

FIELD_TYPE_REGISTRY = {
    "string": StringField,
    "integer": IntegerField,
    "select": SelectField,
    "textarea": TextAreaField,
    "submit": SubmitField,
}


def _build_validators(field_spec: FactSpec) -> list[Any]:
    validators: list[Any] = []
    has_required = False

    for validator_spec in field_spec.validators:
        validator = _resolve_validator(validator_spec)
        if validator_spec.kind == "required":
            has_required = True
        validators.append(validator)

    if field_spec.required and not has_required:
        validators.append(DataRequired())

    return validators


def _resolve_validator(validator_spec: ValidatorSpec) -> Any:
    if validator_spec.kind == "required":
        if validator_spec.message:
            return DataRequired(message=validator_spec.message)
        return DataRequired()

    if validator_spec.kind == "number_range":
        kwargs: dict[str, Any] = {}
        if validator_spec.min_value is not None:
            kwargs["min"] = validator_spec.min_value
        if validator_spec.max_value is not None:
            kwargs["max"] = validator_spec.max_value
        if validator_spec.message:
            kwargs["message"] = validator_spec.message
        return NumberRange(**kwargs)

    raise ValueError(f"Unsupported validator kind: {validator_spec.kind}")


def build_form_class(
    form_name: str,
    schema: tuple[FactSpec, ...],
) -> type[FlaskForm]:
    attrs: dict[str, Any] = {}

    for field_spec in schema:
        field_class = FIELD_TYPE_REGISTRY.get(field_spec.field_type)
        if field_class is None:
            raise ValueError(
                f"Unsupported field type: {field_spec.field_type} ({field_spec.name})"
            )

        if field_spec.field_type == "submit":
            attrs[field_spec.name] = field_class(field_spec.label)
            continue

        kwargs: dict[str, Any] = {
            "validators": _build_validators(field_spec),
        }
        if field_spec.choices:
            kwargs["choices"] = list(field_spec.choices)
        if field_spec.ui:
            kwargs["render_kw"] = dict(field_spec.ui)

        attrs[field_spec.name] = field_class(field_spec.label, **kwargs)

    return type(form_name, (FlaskForm,), attrs)


def build_fact_payload(
    form: FlaskForm,
    schema: tuple[FactSpec, ...],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field_spec in schema:
        if not field_spec.fact_slot:
            continue
        payload[field_spec.fact_slot] = getattr(form, field_spec.name).data
    return payload


def build_session_payload(
    form: FlaskForm,
    schema: tuple[FactSpec, ...],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field_spec in schema:
        if field_spec.field_type == "submit" or not field_spec.include_in_session:
            continue
        value = getattr(form, field_spec.name).data
        payload[field_spec.name] = value or ""
    return payload
