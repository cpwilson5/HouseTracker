from flask import Blueprint

configuration = Blueprint('configuration', __name__)

from . import views
