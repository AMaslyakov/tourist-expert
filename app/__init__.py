import os
from datetime import datetime, timezone

from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect

from app.forms import LandingForm
from app.rules import TravelRuleEngine, init_rule_engine
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
                recommendation_text = engine.evaluate(
                    climate=form.climate.data,
                    travel_type=form.travel_type.data,
                    companions=form.companions.data,
                    budget_rub=form.budget_rub.data,
                    trip_days=form.trip_days.data,
                )
                save_consultation_session(
                    {
                        "created_at_utc": datetime.now(timezone.utc).isoformat(),
                        "input": {
                            "departure_city": form.departure_city.data,
                            "budget_rub": int(form.budget_rub.data),
                            "trip_days": int(form.trip_days.data),
                            "climate": form.climate.data,
                            "travel_type": form.travel_type.data,
                            "companions": form.companions.data,
                            "notes": form.notes.data or "",
                        },
                        "recommendation": recommendation_text,
                    }
                )
        return render_template(
            "index.html",
            form=form,
            recommendation_text=recommendation_text,
        )

    return app
