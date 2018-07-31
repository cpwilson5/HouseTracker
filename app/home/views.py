from flask import render_template, redirect, url_for
from flask_login import login_required
from flask_pymongo import PyMongo
from ..helpers import flash_errors
import os

from . import home

@home.route('/')
def homepage():
    """
    Render the homepage template on the / route
    """
    #return render_template('home/index.html', title="Welcome")
    return redirect(url_for('account.login'))

@home.route('/features')
def features():
    """
    Render the homepage template on the / route
    """
    #return render_template('home/features.html', title="Welcome")
    return redirect(url_for('account.login'))

@home.route('/pricing')
def pricing():
    """
    Render the homepage template on the / route
    """
    #return render_template('home/pricing.html', title="Welcome")
    return redirect(url_for('account.login'))

@home.route('/dashboard')
@login_required
def dashboard():
    """
    Render the dashboard template on the /dashboard route
    """
    #return render_template('home/dashboard.html', title="Dashboard")
    return redirect(url_for('account.login'))
