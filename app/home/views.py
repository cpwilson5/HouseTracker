from flask import render_template
from flask_login import login_required
from flask_pymongo import PyMongo
from ..helpers import flash_errors

from . import home

@home.route('/')
def homepage():
    """
    Render the homepage template on the / route
    """
    print("hey")
    print(os.environ.get('IS_HEROKU'))
    print(os.environ.get('SECRET_KEY'))
    return render_template('home/index.html', title="Welcome")

@home.route('/features')
def features():
    """
    Render the homepage template on the / route
    """
    return render_template('home/features.html', title="Welcome")

@home.route('/pricing')
def pricing():
    """
    Render the homepage template on the / route
    """
    return render_template('home/pricing.html', title="Welcome")

@home.route('/dashboard')
@login_required
def dashboard():
    """
    Render the dashboard template on the /dashboard route
    """
    return render_template('home/dashboard.html', title="Dashboard")
