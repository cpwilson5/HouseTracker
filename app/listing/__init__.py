from flask import Blueprint
import dateutil.parser
import datetime
import pytz
from pytz import timezone

listing = Blueprint('listing', __name__)

from . import views

### https://www.michaelcho.me/article/custom-jinja-template-filters-in-flask ###
@listing.app_template_filter()
def pretty_date(value, format="%a, %b %-d at %-I:%M %p EST"):
    if isinstance(value, datetime.date): # if it's a date time then just set the value (due_date)
        obj = value # else assume it's already datetime
    else: # else if it's a string then convert to datetime (update_date and create_date)
        obj = dateutil.parser.parse(value)

    # ensure midnight doesn't show up on listing steps
    # since no time was really entered and midnight is just default
    #if obj.time() == datetime.time(0, 0):
    #    format = '%A, %B %-d'

    return obj.strftime(format)
