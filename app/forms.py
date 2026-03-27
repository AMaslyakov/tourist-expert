from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange


class LandingForm(FlaskForm):
    departure_city = StringField(
        "Город отправления",
        validators=[DataRequired(message="Укажите город отправления.")],
    )
    budget_rub = IntegerField(
        "Бюджет (руб.)",
        validators=[
            DataRequired(message="Укажите бюджет."),
            NumberRange(min=1000, message="Бюджет должен быть не меньше 1000 руб."),
        ],
    )
    trip_days = IntegerField(
        "Длительность (дней)",
        validators=[
            DataRequired(message="Укажите длительность поездки."),
            NumberRange(min=1, max=60, message="Допустимый диапазон: от 1 до 60 дней."),
        ],
    )
    climate = SelectField(
        "Предпочитаемый климат",
        choices=[
            ("any", "Без предпочтений"),
            ("warm", "Теплый"),
            ("mild", "Умеренный"),
            ("cold", "Прохладный"),
        ],
        validators=[DataRequired()],
    )
    travel_type = SelectField(
        "Тип отдыха",
        choices=[
            ("relax", "Спокойный"),
            ("active", "Активный"),
            ("mixed", "Смешанный"),
            ("culture", "Культурный"),
        ],
        validators=[DataRequired()],
    )
    companions = SelectField(
        "Состав поездки",
        choices=[
            ("solo", "Один"),
            ("couple", "Пара"),
            ("family", "Семья"),
            ("friends", "Друзья"),
        ],
        validators=[DataRequired()],
    )
    notes = TextAreaField("Дополнительные пожелания")
    submit = SubmitField("Начать консультацию")
