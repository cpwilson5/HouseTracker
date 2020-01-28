from flask import render_template
from flask_login import login_required, current_user
from flask import request, redirect, render_template, url_for, flash, current_app as app
from flask_pymongo import PyMongo
from .forms import ProjectForm, ProjectStepForm
from ..account.forms import InviteForm
from .models import Project, ProjectStep
from ..account.models import User, Template, TemplateStep, Account
from bson import ObjectId
from ..utils import s3_upload, s3_retrieve, send_sms, send_email
from ..helpers import flash_errors, confirm_token, send_invitation, distro, pretty_date
from ..decorators import admin_login_required
import datetime
import json

from . import project

@project.route('/projects')
@login_required
@admin_login_required
def projects():

    if request.args.get('sort') == 'closing':
        sort = 'close_date'
        order = 1
    elif request.args.get('sort') == 'created':
        sort = 'create_date'
        order = -1
    elif request.args.get('sort') == 'inactive':
        sort = 'update_date'
        order = 1
    else:
        sort = 'update_date'
        order = -1

    if request.args.get('completed') == 'true':
        complete = True
    else:
        complete = False

    projects = Project.all(active=True, complete=complete, sort=sort, order=order)
    count = projects.count(True)
    return render_template('project/projects.html', projects=projects, count=count, title="Welcome")

@project.route('/projects/add', methods=['GET', 'POST'])
@login_required
@admin_login_required
def add_project():
    form = ProjectForm()
    if request.method == 'GET':
        templates = Template.all(current_user.get_account())
        form.template.choices = [("111111111111111111111111", "Use a template...")] + [(template['_id'], template['name']) for template in templates]

    if request.method == 'POST' and form.validate_on_submit():
        if form.photo.data:
            s3_filepath = s3_upload(form.photo, 'photo')
        else:
            s3_filepath = None

        if form.close_date.data is None:
            date_time = ''
        elif form.close_time.data is None:
            date_time = datetime.datetime.combine(form.close_date.data, datetime.time.min)
        else:
            date_time = datetime.datetime.combine(form.close_date.data, form.close_time.data)

        project = Project(form.name.data, form.address1.data, \
        form.address2.data, form.city.data, form.state.data, form.zip.data, \
        date_time, photo=s3_filepath)
        project_id = project.add()

        # Add user's template steps to new project
        template_steps = list(TemplateStep.all(form.template.data))
        template_steps_count = template_steps.count(True)
        for template_step in template_steps:
            # takes the account steps and derives the new date based on the close date
            if 'days_before_close' in template_step['steps'] and form.close_date.data:
                days_before_close = template_step['steps']['days_before_close']

                if days_before_close:
                    due_date = form.close_date.data - datetime.timedelta(days=days_before_close)
                    due_date_time = datetime.datetime.combine(due_date, datetime.datetime.min.time())
                else:
                    due_date_time = None
            else:
                due_date_time = None

            name = template_step['steps']['name'] if 'name' in template_step['steps'] else None
            notes = template_step['steps']['notes'] if 'notes' in template_step['steps'] else None

            project_step = ProjectStep(project_id, name=name, notes=notes, due_date=due_date_time, status='red')
            project_step.add()
        flash("Successfully created %s with %s steps" % (form.name.data, template_steps_count), category='success')
        return redirect(url_for('project.project_steps', id=project_id))
    else:
        flash_errors(form)
    return render_template('project/project.html', id=[], form=form)

@project.route('/projects/edit/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_project(id):
    form = ProjectForm()
    project = Project.get(id)

    if request.method == 'GET':
        form.name.data = project['name']
        form.address1.data = project['address1']
        form.address2.data = project['address2']
        form.city.data = project['city']
        form.state.data = project['state']
        form.zip.data = project['zip']
        form.close_date.data = project['close_date'] if project['close_date'] else None
        form.close_time.data = project['close_date'] if project['close_date'] and (project['close_date'].hour != 0 and project['close_date'] != 0) else None
        photo = project['photo'] if 'photo' in project else None

        completed = True if 'complete_date' in project else False

        return render_template('project/project.html', id=id, completed=completed, form=form, photo=photo)

    if request.method == 'POST' and form.validate_on_submit():
        if form.photo.data:
            s3_filepath = s3_upload(form.photo, 'photo')
        else:
            s3_filepath = None

        if form.close_date.data is None:
            date_time = ''
        elif form.close_time.data is None:
            date_time = datetime.datetime.combine(form.close_date.data, datetime.time.min)
        else:
            date_time = datetime.datetime.combine(form.close_date.data, form.close_time.data)

        Project.update(id, form.name.data, form.address1.data, \
        form.address2.data, form.city.data, form.state.data, form.zip.data, \
        date_time, photo=s3_filepath)

        # compare changes to provide details in text/email
        if project['close_date']:
            db_close_date = project['close_date'].replace(tzinfo=None)
        else:
            db_close_date = None

        if date_time != db_close_date and form.close_date.data:
            # build body of email/text based on what changed and email/text only if changes
            email_body = "You're closing date has been updated to " + pretty_date(date_time) + "<br><br>"
            text_body = "You're closing date has been updated to " + pretty_date(date_time) + ".\n\n"

            email_body = email_body + "<br>Login for more details: " + url_for('account.login', _external=True)
            text_body = text_body + "\nLogin here: " + url_for('account.login', _external=True)

            # then send email updates only if there are changes
            email_users = User.all(project=id, email_alert=True)
            email_distro = distro(email_users, 'email')
            if email_distro:
                send_email(email_distro, "You're project has been updated", email_body)

            # send text update
            text_users = User.all(project=id, text_alert=True)
            text_distro = distro(text_users, 'cell')
            if text_distro:
                send_sms(text_distro, text_body)
        # otherwise don't send an email or text if closing date didn't change

        flash("Updated project", category='success')
        return redirect(url_for('project.project_steps', id=id))
    else:
        flash_errors(form)
        return render_template('project/project.html', id=id, form=form)

@project.route('/photo/<string:photo>', methods=['GET'])
@login_required
def get_photo(photo):
    return redirect(s3_retrieve(photo, 'photo'))

@project.route('/projects/delete/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def delete_project(id):
    Project.delete(id)
    flash("Project deleted", category='success')
    return redirect(url_for('project.projects'))

@project.route('/projects/complete/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def complete_project(id):
    Project.complete(id)
    flash("Congrats!  Your project has been closed", category='success')
    return redirect(url_for('project.projects'))

@project.route('/projects/reactivate/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def reactivate_project(id):
    Project.reactivate(id)
    flash("Project has been reactivated", category='success')
    return redirect(url_for('project.projects'))

@project.route('/projects/<string:id>/steps')
@login_required
@admin_login_required
def project_steps(id):
    project_steps = list(ProjectStep.all(id, active=True, include_complete=True))
    if not project_steps:
        project_steps = []

    # have to convert to list so i can iterate over users and pass users to template
    users = list(User.all(project=id))
    clients_count = sum(1 for user in users if user['role']=='client')
    partners_count = sum(1 for user in users if user['role']=='partner')

    project = Project.get(id)
    realtor = User.get(accounts_realtor=current_user.get_account())

    if project['close_date']:
        days_left = (project['close_date'].date() - datetime.datetime.now().date()).days
        if days_left < 0:
            days_left = 0
    else:
        days_left = -1
    return render_template('project/projectsteps.html', id=id, project_steps=project_steps, users=users, project=project, realtor=realtor, days_left=days_left, partners_count=partners_count, clients_count=clients_count)

@project.route('/projects/<string:id>/steps/add', methods=['GET', 'POST'])
@login_required
@admin_login_required
def add_project_step(id):
    form = ProjectStepForm()
    if request.method == 'POST' and form.validate_on_submit():
        if form.attachment.data:
            s3_filepath = s3_upload(form.attachment, 'attachment')
        else:
            s3_filepath = None

        if form.due_date.data is None:
            date_time = ''
        elif form.time.data is None:
            date_time = datetime.datetime.combine(form.due_date.data, datetime.time.min)
        else:
            date_time = datetime.datetime.combine(form.due_date.data, form.time.data)

        project_step = ProjectStep(project_id=id, name=form.name.data, \
        notes=form.notes.data, attachment=s3_filepath, due_date=date_time, \
        status = form.status.data)
        project_step.add()

        # build body of email/text
        email_body = "A project step '" + form.name.data + "' has been added.<br><br>"
        text_body = "A project step '" + form.name.data + "' has been added.\n\n"

        if date_time:
            email_body = email_body + "Scheduled Date: " + pretty_date(date_time) + "<br>"
            text_body = text_body + "Scheduled Date: " + pretty_date(date_time) + "\n"
        if s3_filepath:
            email_body = email_body + "Attachment: Added<br>"
            text_body = text_body + "Attachment: Added\n"

        email_body = email_body + "<br>Login for more details: " + url_for('account.login', _external=True)
        text_body = text_body + "\nLogin here: " + url_for('account.login', _external=True)

        # then send email updates only if there are changes
        email_users = User.all(project=id, email_alert=True)
        email_distro = distro(email_users, 'email')
        if email_distro:
            send_email(email_distro, "You're project has been updated", email_body)

        # send text update
        text_users = User.all(project=id, text_alert=True)
        text_distro = distro(text_users, 'cell')
        if text_distro:
            send_sms(text_distro, text_body)

        flash("Successfully added project step", category='success')
        return redirect(url_for('project.project_steps', id=id))
    else:
        flash_errors(form)
    return render_template('project/projectstep.html', id=id, project_step=[], form=form)

@project.route('/projects/<string:id>/steps/edit/<string:step_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_project_step(id, step_id):
    form = ProjectStepForm()
    project_step = ProjectStep.get(id, step_id)

    if request.method == 'GET':
        form.name.data = project_step['steps'][0]['name']
        form.notes.data = project_step['steps'][0]['notes']
        form.due_date.data = project_step['steps'][0]['due_date'] if project_step['steps'][0]['due_date'] else None
        form.time.data = project_step['steps'][0]['due_date'] if project_step['steps'][0]['due_date'] and (project_step['steps'][0]['due_date'].hour != 0 and project_step['steps'][0]['due_date'] != 0) else None
        form.status.data = project_step['steps'][0]['status'] if 'status' in project_step['steps'][0] else 'Red'
        attachment = project_step['steps'][0]['attachment']
        completed = project_step['steps'][0]['complete_date'] if 'complete_date' in project_step['steps'][0] else False

        return render_template('project/projectstep.html', form=form, attachment=attachment, id=id, step_id=step_id, completed=completed)

    if request.method == 'POST' and form.validate_on_submit():
        if form.attachment.data:
            s3_filepath = s3_upload(form.attachment, 'attachment')
        else:
            s3_filepath = None

        if form.due_date.data is None:
            date_time = ''
        elif form.time.data is None:
            date_time = datetime.datetime.combine(form.due_date.data, datetime.time.min)
        else:
            date_time = datetime.datetime.combine(form.due_date.data, form.time.data)

        # update project step
        ProjectStep.update(id=id, step_id=step_id, name=form.name.data, \
        notes=form.notes.data, attachment=s3_filepath, due_date=date_time, \
        status=form.status.data)

        # compare changes to provide details in text/email
        name_changed = False if form.name.data == project_step['steps'][0]['name'] else True
        notes_changed = False if form.notes.data == project_step['steps'][0]['notes'] else True
        status_changed = False if form.status.data == project_step['steps'][0]['status'] else True
        attachment_changed = False if not s3_filepath else True

        # 5 scenarios for dates
            #1 same date to same date - don't send
            #2 date existed to new date - send
            #3 date existed to no date - don't send
            #4 no date to new date - send
            #5 no date to no date - don't send

        # check if an old date existed
        # setting to variable makes it cleaner to read
        if project_step['steps'][0]['due_date']:
            old_date = True
        else:
            old_date = False

        # check if a new date exists to tell us if we should text/email
        if date_time:
            new_date = True
        else:
            new_date = False

        due_date_changed = False

        # if there was a date and there is a new date
        if old_date and new_date:
            # compare dates
            #1 if the same don't do anything
            if date_time == project_step['steps'][0]['due_date'].replace(tzinfo=None):
                due_date_changed = False
            #2 otherwise we need to send alert
            else:
                due_date_changed = True
        #3 otherwise if there was a date but the date was removed
        elif old_date and not new_date:
            due_date_changed = False
        #4
        elif not old_date and new_date:
            due_date_changed = True
        #5
        elif not old_date and not new_date:
            due_date_changed = False

        # build body of email/text based on what changed and email/text only if changes
        if due_date_changed or attachment_changed:
            if name_changed:
                email_body = "You're project step \'" + project_step['steps'][0]['name'] + \
                    "\' has been updated to '" + form.name.data + "\'.<br><br>"
                text_body = "A project step '" + form.name.data + "' has been updated.\n\n"
            else:
                email_body = "You're project step '" + form.name.data + "' has been updated.<br><br>"
                text_body = "A project step '" + form.name.data + "' has been updated.\n\n"

            email_body = email_body + " The following changes were updated: <br>"

            if notes_changed:
                email_body = email_body + "Notes: " + form.notes.data + "<br>"
                text_body = text_body + "Notes: Updated\n"
            if due_date_changed:
                email_body = email_body + "Scheduled Date: " + pretty_date(date_time) + "<br>"
                text_body = text_body + "Scheduled Date: " + pretty_date(date_time) + "\n"
            if status_changed:
                email_body = email_body + "Status: " + form.status.data.capitalize() + "<br>"
                text_body = text_body + "Status: " + form.status.data.capitalize() + "\n"
            if attachment_changed:
                email_body = email_body + "Attachment: Added<br>"
                text_body = text_body + "Attachment: Added\n"

            email_body = email_body + "<br>Login for more details: " + url_for('account.login', _external=True)
            text_body = text_body + "\nLogin here: " + url_for('account.login', _external=True)

            # then send email updates only if there are changes
            email_users = User.all(project=id, email_alert=True)
            email_distro = distro(email_users, 'email')
            if email_distro:
                send_email(email_distro, "You're project has been updated", email_body)

            # send text update
            text_users = User.all(project=id, text_alert=True)
            text_distro = distro(text_users, 'cell')
            if text_distro:
                send_sms(text_distro, text_body)
        # otherwise don't send an email or text if nothing changed
        flash("Successfully updated project step", category='success')
        return redirect(url_for('project.project_steps', id=id))
    else:
        flash_errors(form)
        return redirect(url_for('project.edit_project_step', id=id, project_step=project_step, step_id=step_id))


@project.route('/attachment/<string:attachment>', methods=['GET'])
@login_required
def get_attachment(attachment):
    return redirect(s3_retrieve(attachment, 'attachment'))

@project.route('/projects/<string:id>/steps/delete/<string:step_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def delete_project_step(id, step_id):
    ProjectStep.delete(id, step_id)
    return redirect(url_for('project.project_steps', id=id))

@project.route('/projects/<string:id>/steps/complete/<string:step_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def complete_project_step(id, step_id):
    ProjectStep.complete(id, step_id)
    return redirect(url_for('project.project_steps', id=id))

@project.route('/projects/<string:id>/steps/sort', methods=['POST'])
@login_required
def sort_project_step(id):
    ProjectStep.sort(id, request.form['order'])
    return json.dumps({'status':'Successfully sorted'})

### adding a project viewer (client/partner) ###
@project.route('/projects/<string:id>/<string:role>/invite', methods=['GET', 'POST'])
@login_required
def invite_viewer(id, role):
    form = InviteForm()

    if request.method == 'GET':
        return render_template('project/viewer.html', id=id, user=[], user_role=role, form=form)

    if request.method == 'POST' and form.validate_on_submit():
        existing_user = User.get(email=form.email.data)
        realtor = User.get(accounts_realtor=current_user.get_account())

        try:
            if existing_user is None:
                send_invitation(form.email.data, realtor=realtor, new_user=True)

                if role == 'partner': # it's a partner
                    text_alert = False
                    email_alert = False
                else: # it's a client
                    text_alert = False ## Update this line to True when we buy Twilio
                    email_alert = True

                User.add(form.email.data, form.first_name.data, form.last_name.data, \
                    current_user.get_account(), role, invited_by=current_user.get_id(), \
                    confirmed=False, project=[id], email_alert=email_alert, text_alert=text_alert, \
                    partner_type=form.partner_type.data)
            else:
                send_invitation(form.email.data, realtor=realtor, new_user=False)
                User.update(existing_user['_id'], form.email.data, project=id)

            flash("Invitation sent", category='success')
            return redirect(url_for('project.project_steps', id=id))
        except:
            flash("Error inviting viewer", category='danger')
            return render_template('project/viewer.html', id=id, form=form)
    else:
        flash_errors(form)
        return render_template('project/viewer.html', id=id, user=[], form=form)

@project.route('/projects/<string:id>/viewers/edit/<string:viewer_id>', methods=['GET', 'POST'])
@login_required
def edit_viewer(id, viewer_id):
    form = InviteForm()
    user = User.get(id=viewer_id)
    user_role = user['role']

    if request.method == 'GET':
        form.first_name.data = user['first_name']
        form.last_name.data = user['last_name']
        form.email.data = user['email']
        form.cell.data = user['cell']
        form.partner_type.data = user['partner_type'] if 'partner_type' in user else None

        return render_template('project/viewer.html', id=id, user=user, user_role=user_role, form=form)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            realtor = User.get(accounts_realtor=current_user.get_account())
            print(form.partner_type.data)
            User.update(viewer_id, form.email.data, form.first_name.data, form.last_name.data, form.cell.data, partner_type=form.partner_type.data)
            send_invitation(form.email.data, realtor=realtor, new_user=True)
            flash("Invitation resent", category='success')
        except:
            flash("Error inviting viewer", category='danger')
            return render_template('project/viewer.html', form=form, user=user, user_role=user_role)

        return redirect(url_for('project.project_steps', id=id))
    else:
        flash_errors(form)
        return render_template('project/viewer.html', id=id, user=[], user_role=user_role, form=form)

@project.route('/projects/<string:id>/viewers/delete/<string:viewer_id>', methods=['GET', 'POST'])
@login_required
def delete_viewer(id, viewer_id):
    User.delete(id=viewer_id, context='viewer', project=id)
    flash("User removed succesfully", category='success')
    return redirect(url_for('project.project_steps', id=id))
