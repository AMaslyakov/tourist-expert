from __future__ import annotations

import os

from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFProtect

from app.forms import (
    LandingForm,
    SUBMIT_FIELD_NAME,
    VISIBLE_FORM_FIELDS,
)
from app.rules import init_rule_engine
from app.services import build_consultation_outcome, build_test_route_context
from app.session_store import get_consultation_dir, save_consultation_session

csrf = CSRFProtect()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-local-secret")
    app.config["DEBUG"] = False
    app.config["WTF_CSRF_ENABLED"] = True

    csrf.init_app(app)
    init_rule_engine(app)
    get_consultation_dir()

    @app.route("/", methods=["GET", "POST"])
    def index() -> str:
        form = LandingForm()
        recommendation_text = None

        if form.validate_on_submit():
            engine = app.extensions["expert_engine"]
            outcome = build_consultation_outcome(form, engine)
            recommendation_text = outcome.recommendation_text
            if outcome.session_payload is not None:
                save_consultation_session(outcome.session_payload)

        return render_template(
            "index.html",
            form=form,
            visible_fields=VISIBLE_FORM_FIELDS,
            submit_field_name=SUBMIT_FIELD_NAME,
            recommendation_text=recommendation_text,
        )

    @app.route("/test", methods=["GET"])
    def test_route() -> str:
        run_tests = request.args.get("run_tests") == "1"
        engine = app.extensions["expert_engine"]
        context = build_test_route_context(engine, run_tests)
        return render_template("test.html", **context)

    return app
