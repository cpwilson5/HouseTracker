from flask import render_template
from flask_login import login_required, current_user
from flask import request, redirect, render_template, url_for, flash, current_app
from flask_pymongo import PyMongo
from ..account.forms import TemplateForm, TemplateStepForm
from ..account.models import User
from .models import AppTemplate, AppTemplateStep
from bson import ObjectId
from ..helpers import flash_errors
from ..decorators import admin_login_required
import json

from . import configuration

### Templates ###

@configuration.route('/apptemplates')
@login_required
@admin_login_required
def app_templates():
    templates = AppTemplate.all()
    count = templates.count(True)
    return render_template('configuration/apptemplates.html', templates=templates, count=count)

@configuration.route('/apptemplates/add', methods=['GET', 'POST'])
@login_required
@admin_login_required
def add_app_template():
    form = TemplateForm()
    if request.method == 'POST' and form.validate_on_submit():
        template = AppTemplate(form.name.data)
        id = template.add()
        return redirect(url_for('configuration.app_template_steps', id=id))
    else:
        flash_errors(form)
    return render_template('configuration/apptemplate.html', template=[], form=form)

@configuration.route('/apptemplates/edit/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_app_template(id):
    form = TemplateForm()

    if request.method == 'GET':
        template = AppTemplate.get(id)
        form.name.data = template['name']

    if request.method == 'POST' and form.validate_on_submit():
        AppTemplate.update(id, form.name.data)
        return redirect(url_for('configuration.apptemplates'))
    else:
        flash_errors(form)
    return render_template('configuration/apptemplate.html', id=id, template=template, form=form)

@configuration.route('/apptemplates/delete/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def delete_app_template(id):
    AppTemplate.delete(id)
    flash("Template removed succesfully", category='success')
    return redirect(url_for('configuration.app_templates'))


### Template Steps ###

@configuration.route('/apptemplates/<string:id>/steps', methods=['GET', 'POST'])
@login_required
@admin_login_required
def app_template_steps(id):
    template = AppTemplate.get(id)
    template_steps = AppTemplateStep.all(id)
    # this is weird but I had to get the cursor twice
    # because whenever I used "list" it would replace my template_steps_list
    # even when I just was referencing the variable
    template_steps_list = AppTemplateStep.all(id)
    count = len(list(template_steps_list))

    # this is edit template but we're doing it in a modal since it's just a name
    form = TemplateForm()

    if request.method == 'GET':
        form.name.data = template['name']

    if request.method == 'POST' and form.validate_on_submit():
        AppTemplate.update(id, form.name.data)
        return redirect(url_for('configuration.app_template_steps', id=id))
    else:
        flash_errors(form)

    return render_template('configuration/apptemplatesteps.html', form=form, id=id, template=template, template_steps=template_steps, count=count)

@configuration.route('/apptemplates/<string:id>/steps/add', methods=['GET', 'POST'])
@login_required
@admin_login_required
def add_app_template_step(id):
    form = TemplateStepForm()
    if request.method == 'POST' and form.validate_on_submit():
        template_step = AppTemplateStep(id, form.name.data, form.notes.data, form.days_before_close.data)
        template_step.add()
        return redirect(url_for('configuration.app_template_steps', id=id))
    else:
        flash_errors(form)
    return render_template('configuration/apptemplatestep.html', template_step=[], id=id, form=form)

@configuration.route('/apptemplates/<string:id>/steps/edit/<string:step_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_app_template_step(id, step_id):
    form = TemplateStepForm()

    if request.method == 'GET':
        template_step = AppTemplateStep.get(id, step_id)
        form.name.data = template_step['steps'][0]['name']
        form.notes.data = template_step['steps'][0]['notes']
        form.days_before_close.data = template_step['steps'][0]['days_before_close'] if 'days_before_close' in template_step['steps'][0] else None
        return render_template('configuration/apptemplatestep.html', id=id, step_id=step_id, template_step=template_step, form=form)

    if request.method == 'POST' and form.validate_on_submit():
        AppTemplateStep.update(id, step_id, form.name.data, form.notes.data, form.days_before_close.data)
        return redirect(url_for('configuration.app_template_steps', id=id))
    else:
        flash_errors(form)
        return render_template('configuration/apptemplatestep.html', id=id, step_id=step_id, template_step=[], form=form)

@configuration.route('/apptemplates/<string:id>/steps/delete/<string:step_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def delete_app_template_step(id, step_id):
    AppTemplateStep.delete(id, step_id)
    flash("Step removed succesfully", category='success')
    return redirect(url_for('configuration.app_template_steps', id=id))

@configuration.route('/apptemplates/<string:id>/steps/sort', methods=['POST'])
@login_required
def sort_app_template_step(id):
    AppTemplateStep.sort(id, request.form['order'])
    return json.dumps({'status':'Successfully sorted'})
