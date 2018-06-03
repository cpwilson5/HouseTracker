from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.fields.html5 import DateField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from wtforms.validators import DataRequired

class ListingForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    address1 = StringField('Address1', validators=[DataRequired()])
    address2 = StringField('Address2')
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    zip = StringField('Zip', validators=[DataRequired()])

class ListingStepForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    notes = StringField('Notes')
    due_date = DateField('Due Date', format='%Y-%m-%d')
    attachment = FileField('Attachment', validators=[FileAllowed(['jpg', 'png', 'pdf'], 'Must be JPG, PNG or PDF')])
