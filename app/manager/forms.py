from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, TextAreaField,
                     DateField, TimeField, SubmitField, IntegerField,
                     SelectMultipleField)
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange


PPE_OPTIONS = [
    "Safety glasses",
    "Hearing protection",
    "Gloves",
    "Hard hat",
    "Hi-vis vest",
    "Long sleeves",
    "Hairnets",
    "Beard nets",
    "Smocks",
]

PPE_ICONS = {
    "Safety glasses": "🥽",
    "Hearing protection": "🎧",
    "Gloves": "🧤",
    "Hard hat": "⛑️",
    "Hi-vis vest": "🦺",
    "Long sleeves": "👕",
    "Hairnets": "🧢",
    "Beard nets": "🧔",
    "Smocks": "🥼",
}


class EmployeeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=150)
    ])
    password = PasswordField('Password', validators=[Optional(), Length(min=6, max=150)])
    role = SelectField('Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')


class RouteForm(FlaskForm):
    name = StringField('Route Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    ppe_required = SelectMultipleField(
        'PPE Required',
        choices=[(item, item) for item in PPE_OPTIONS],
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput(),
        validators=[Optional()],
    )
    submit = SubmitField('Save')


class ShiftForm(FlaskForm):
    user_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    route_id = SelectField('Route', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save')


class StopForm(FlaskForm):
    name = StringField('Stop Name', validators=[DataRequired(), Length(max=150)],
                       render_kw={"placeholder": "e.g. Nucor Steel Crawfordsville"})
    address = StringField('Address', validators=[Optional(), Length(max=255)],
                          render_kw={"placeholder": "e.g. 4200 N US-231, Crawfordsville, IN"})
    notes = TextAreaField('Notes', validators=[Optional()],
                          render_kw={"placeholder": "Gate codes, parking instructions, hazards..."})
    submit = SubmitField('Save')


class RouteStopForm(FlaskForm):
    stop_id = SelectField('Stop', coerce=int, validators=[DataRequired()])
    day = SelectField('Day', coerce=int, validators=[DataRequired()],
                      choices=[(1, 'Day 1'), (2, 'Day 2'), (3, 'Day 3'), (4, 'Day 4')])
    sequence = IntegerField('Order in Day', validators=[Optional(), NumberRange(min=0)],
                            default=0,
                            render_kw={"placeholder": "0 = first, 1 = second..."})
    notes = TextAreaField('Stop Notes for This Route', validators=[Optional()],
                          render_kw={"placeholder": "Route-specific instructions for this stop"})
    submit = SubmitField('Add Stop')
