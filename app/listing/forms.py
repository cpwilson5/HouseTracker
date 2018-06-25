from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.fields.html5 import DateField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.widgets import TextArea
from werkzeug.utils import secure_filename
from wtforms.validators import DataRequired, Optional
from datetime import datetime, timedelta

STATE_ABBREV = ('AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IO', 'KS', 'KY', 'LA', 'MA', 'MD',
                'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH',
                'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY')

class ListingForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    address1 = StringField('Address1', validators=[DataRequired()])
    address2 = StringField('Address2')
    city = StringField('City', validators=[DataRequired()])
    state = SelectField('State', choices=[(state, state) for state in STATE_ABBREV], validators=[DataRequired()])
    zip = StringField('Zip', validators=[DataRequired()])
    close_date = DateField('Closing Date', format='%Y-%m-%d', \
        default=datetime.today()+timedelta(days=30), validators=[DataRequired()])
    photo = FileField('Photo', validators=[FileAllowed(['jpg', 'jpeg', 'gif', 'bmp', 'png'], 'Must be JPG, JPEG, GIF, BMP or PNG')])

class ListingStepForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    notes = StringField('Notes',widget=TextArea())
    due_date = DateField('Due Date', format='%Y-%m-%d', \
        default=datetime.today(), validators=[Optional()])
    status = SelectField('Status', choices=[('green','Green'),('yellow','Yellow'),('red','Red')])
    attachment = FileField('Attachment', validators=[FileAllowed(['jpg', 'jpeg', 'gif', 'bmp', 'png', 'pdf'], 'Must be JPG, JPEG, GIF, BMP, PNG or PDF')])
