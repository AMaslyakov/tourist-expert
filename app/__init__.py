from __future__ import annotations

import os
from datetime import datetime, timezone

from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFProtect

from app.forms import (
    LandingForm,
    SUBMIT_FIELD_NAME,
    VISIBLE_FORM_FIELDS,
    get_evaluation_input,
    get_session_input,
)
from app.prototype_testing import (
    build_prototype_testing_context,
    get_prototype_scenario_previews,
)
from app.rules import EvaluationResult, TravelRuleEngine, init_rule_engine
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
            if isinstance(engine, TravelRuleEngine):
                evaluation_input = get_evaluation_input(form)
                evaluation_result = engine.evaluate(evaluation_input, explain=True)

                if isinstance(evaluation_result, EvaluationResult):
                    recommendation_text = evaluation_result.recommendation
                    backward_result = engine.backward(
                        goal="*",
                        known_facts=evaluation_input,
                        explain=True,
                    )
                    save_consultation_session(
                        {
                            "created_at_utc": datetime.now(timezone.utc).isoformat(),
                            "input": get_session_input(form),
                            "recommendation": recommendation_text,
                            "explain": {
                                "forward": {
                                    "matched_rules": list(evaluation_result.matched_rules),
                                    "selected_rule": evaluation_result.selected_rule,
                                    "elapsed_ms": evaluation_result.elapsed_ms,
                                    "passes": evaluation_result.passes,
                                    "steps": list(evaluation_result.steps),
                                },
                                "backward": {
                                    "goal": backward_result.goal,
                                    "achieved": backward_result.achieved,
                                    "selected_rule": backward_result.selected_rule,
                                    "matched_rules": list(backward_result.matched_rules),
                                    "recommendation": backward_result.recommendation,
                                    "elapsed_ms": backward_result.elapsed_ms,
                                    "passes": backward_result.passes,
                                    "steps": list(backward_result.steps),
                                    "proof": backward_result.proof,
                                },
                            },
                        }
                    )

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
        if not isinstance(engine, TravelRuleEngine):
            return render_template(
                "test.html",
                engine_error=True,
                run_tests=run_tests,
                scenario_previews=get_prototype_scenario_previews(),
            )

        test_context: dict[str, object] = {}
        if run_tests:
            test_context = build_prototype_testing_context(engine)

        return render_template(
            "test.html",
            engine_error=False,
            run_tests=run_tests,
            rules_count=engine.rules_count(),
            scenario_previews=get_prototype_scenario_previews(),
            **test_context,
        )

    return app
