from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.fields.html5 import DateField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.widgets import TextArea
from werkzeug.utils import secure_filename
from wtforms.validators import DataRequired, Optional
from datetime import datetime, timedelta

class ListingForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    address1 = StringField('Address1', validators=[DataRequired()])
    address2 = StringField('Address2')
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    zip = StringField('Zip', validators=[DataRequired()])
    close_date = DateField('Closing Date', format='%Y-%m-%d', \
        default=datetime.today()+timedelta(days=30), validators=[DataRequired()])

class ListingStepForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    notes = StringField('Notes',widget=TextArea())
    due_date = DateField('Due Date', format='%Y-%m-%d', \
        default=datetime.today(), validators=[Optional()])
    color = SelectField('Color', choices=[('Green','Green'),('Yellow','Yellow'),('Red','Red')])
    attachment = FileField('Attachment', validators=[FileAllowed(['jpg', 'png', 'pdf'], 'Must be JPG, PNG or PDF')])
