from flask import render_template
from flask_login import login_required, current_user
from flask import request, redirect, render_template, url_for, flash, current_app
from flask_pymongo import PyMongo
from .forms import AppStepForm
from ..account.models import User
from .models import AppStep
from bson import ObjectId
from ..helpers import flash_errors
from ..decorators import admin_login_required
import json

from . import configuration

@configuration.route('/appsteps')
@login_required
@admin_login_required
def app_steps():
    app_steps = AppStep.all()
    return render_template('configuration/appsteps.html', app_steps=app_steps, title="Welcome")

@configuration.route('/appsteps/add', methods=['GET', 'POST'])
@login_required
@admin_login_required
def add_app_step():
    form = AppStepForm()
    if request.method == 'POST' and form.validate_on_submit():
        app_step = AppStep(form.name.data, form.notes.data, form.days_before_close.data)
        app_step.add()
        return redirect(url_for('configuration.app_steps'))
    else:
        flash_errors(form)
    return render_template('configuration/appstep.html', form=form)

@configuration.route('/appsteps/edit/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_app_step(id):
    form = AppStepForm()

    if request.method == 'GET':
        step = AppStep.get(id)
        form.name.data = step['name']
        form.notes.data = step['notes']
        form.days_before_close.data = step['days_before_close'] if 'days_before_close' in step else None

    if request.method == 'POST' and form.validate_on_submit():
        AppStep.update(id, form.name.data, form.notes.data, form.days_before_close.data)
        return redirect(url_for('configuration.app_steps'))
    else:
        flash_errors(form)
    return render_template('configuration/appstep.html', id=id, form=form)

@configuration.route('/appsteps/delete/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def delete_app_step(id):
        AppStep.delete(id)
        return redirect(url_for('configuration.app_steps'))

@configuration.route('/appsteps/sort', methods=['POST'])
@login_required
def sort_app_step():
    AppStep.sort(request.form['order'])
    return json.dumps({'status':'Successfully sorted'})
