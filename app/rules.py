from __future__ import annotations

from typing import TYPE_CHECKING

import clips

if TYPE_CHECKING:
    from flask import Flask


class TravelRuleEngine:
    """Базовый модуль продукционных правил на clipspy (CLIPS)."""

    def __init__(self) -> None:
        self.environment = clips.Environment()
        self._load_knowledge_base()

    def _load_knowledge_base(self) -> None:
        constructs = [
            """
            (deftemplate travel-input
              (slot climate)
              (slot travel_type)
              (slot companions)
              (slot budget_rub (type INTEGER))
              (slot trip_days (type INTEGER)))
            """,
            """
            (deftemplate recommendation
              (slot text))
            """,
            """
            (defrule warm-relax-premium
              (travel-input
                (climate warm)
                (travel_type relax)
                (budget_rub ?b&:(>= ?b 100000)))
              =>
              (assert (recommendation
                (text "Рекомендуется пляжный отдых в теплой стране с повышенным уровнем комфорта."))))
            """,
            """
            (defrule active-short-budget
              (travel-input
                (travel_type active)
                (budget_rub ?b&:(< ?b 100000))
                (trip_days ?d&:(<= ?d 7)))
              =>
              (assert (recommendation
                (text "Рекомендуется активный короткий тур по России или соседним направлениям."))))
            """,
            """
            (defrule family-mild-climate
              (travel-input
                (companions family)
                (climate mild))
              =>
              (assert (recommendation
                (text "Рекомендуется семейный отдых в умеренном климате с короткими переездами."))))
            """,
            """
            (defrule default-recommendation
              (travel-input)
              (not (recommendation))
              =>
              (assert (recommendation
                (text "Рекомендуется универсальный экскурсионный отдых по вашему бюджету и срокам."))))
            """,
        ]

        for construct in constructs:
            self.environment.build(construct)

    def rules_count(self) -> int:
        return sum(1 for _ in self.environment.rules())

    def evaluate(
        self,
        *,
        climate: str,
        travel_type: str,
        companions: str,
        budget_rub: int,
        trip_days: int,
    ) -> str:
        self.environment.reset()
        self.environment.assert_string(
            (
                "(travel-input "
                f"(climate {climate}) "
                f"(travel_type {travel_type}) "
                f"(companions {companions}) "
                f"(budget_rub {int(budget_rub)}) "
                f"(trip_days {int(trip_days)}))"
            )
        )
        self.environment.run()

        for fact in self.environment.facts():
            if fact.template.name == "recommendation":
                return str(fact["text"])

        return "Рекомендация не сформирована. Попробуйте изменить параметры поездки."


def init_rule_engine(app: "Flask") -> TravelRuleEngine:
    engine = TravelRuleEngine()
    app.extensions["expert_engine"] = engine
    return engine
