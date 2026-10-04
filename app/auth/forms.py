from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=150)
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Save')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current password',
                                     validators=[DataRequired()])
    new_password = PasswordField('New password',
                                 validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField('Confirm new password',
                            validators=[DataRequired(),
                                        EqualTo('new_password',
                                                message='Passwords must match')])
    submit = SubmitField('Update password')


class RegisterForm(FlaskForm):
    first_name = StringField('First name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last name', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField('Confirm password',
                            validators=[DataRequired(),
                                        EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Create account')
