from flask import Blueprint
import dateutil.parser
import datetime
import pytz
from pytz import timezone

listing = Blueprint('listing', __name__)

from . import views

### https://www.michaelcho.me/article/custom-jinja-template-filters-in-flask ###
@listing.app_template_filter()
def pretty_date(value, format="%a, %b %-d at %-I:%M %p EST", convert_to_tz=False):
    if isinstance(value, datetime.date): # if it's a date time then just set the value (due_date)
        obj = value # else assume it's already datetime
    else: # else if it's a string then convert to datetime (update_date and create_date)
        obj = dateutil.parser.parse(value)

    if convert: # if we want to convert it from UTC
        tz = pytz.timezone('US/Eastern')  # timezone you want to convert to from UTC
        local_dt = obj.astimezone(tz)
        return local_dt.strftime(format)
    # there are cases right now where we store as UTC
    # and it's really not UTC but rather the local time
    # (this happens on the wtf forms where users enter data)
    else:
        return obj.strftime(format)
