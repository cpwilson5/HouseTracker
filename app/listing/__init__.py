from flask import Blueprint
import dateutil.parser

listing = Blueprint('listing', __name__)

from . import views

### https://www.michaelcho.me/article/custom-jinja-template-filters-in-flask ###
@listing.app_template_filter()
def pretty_date(value, format="%a, %b %-d at %-I:%M %p EST"):
    print value
    obj = dateutil.parser.parse(value)
    return obj.strftime(format)
