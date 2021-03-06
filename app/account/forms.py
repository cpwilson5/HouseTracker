from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Email, Length, Regexp, Optional

class LoginForm(FlaskForm):
    """Login form to access writing and settings pages"""

    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class ImpersonateForm(FlaskForm):
    """Login form to access writing and settings pages"""

    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    impersonate_email = StringField('Email', validators=[DataRequired(), Email()])

class RegForm(FlaskForm):
    """Login form to access writing and settings pages"""

    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    cell = StringField('Cell', validators=[DataRequired(), Regexp('^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$', message="Cell must be 10 digits")])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', validators=[DataRequired()])
    email_alert = BooleanField('Email alert')
    text_alert = BooleanField('Text alert')

class TemplateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])

class TemplateStepForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    days_before_close = IntegerField('Days Before Close', validators=[Optional()])

class UserForm(FlaskForm):
    """Login form to access writing and settings pages"""

    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    cell = StringField('Cell', validators=[DataRequired(), Regexp('^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$', message="Cell must be 10 digits")])
    email_alert = BooleanField('Email alert')
    text_alert = BooleanField('Text alert')

class PasswordForm(FlaskForm):
    """Login form to access writing and settings pages"""

    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', validators=[DataRequired()])

PARTNER_TYPES = ('Attorney', 'Lender', 'Paralegal', 'Stager')

class InviteForm(FlaskForm):
    """Login form to access writing and settings pages"""

    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    cell = StringField('Cell')
    partner_type = SelectField('Type', choices=[(type, type) for type in PARTNER_TYPES], validators=[Optional()])

class ForgotPasswordForm(FlaskForm):
    """Login form to access writing and settings pages"""

    email = StringField('Email', validators=[DataRequired()])

class ResetPasswordForm(FlaskForm):
    """Login form to access writing and settings pages"""

    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', validators=[DataRequired()])
