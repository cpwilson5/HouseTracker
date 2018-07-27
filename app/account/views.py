from flask import render_template
from flask_login import login_user, logout_user, login_required, current_user
from flask import request, redirect, render_template, url_for, flash, current_app
from .forms import TemplateForm, TemplateStepForm, UserForm, InviteForm, RegForm, LoginForm, ImpersonateForm, PasswordForm, ForgotPasswordForm, ResetPasswordForm
from .models import User, Account, Template, TemplateStep
from ..configuration.models import AppTemplate, AppTemplateStep
from ..helpers import flash_errors, confirm_token, send_invitation, send_reset
from ..decorators import admin_login_required
import json

from . import account

@account.route('/register', methods=['GET', 'POST'])
def register():
    form = RegForm()

    if request.method == 'POST' and form.validate_on_submit():
        existing_user = User.get(email=form.email.data)
        if existing_user is None:
            account = Account(form.first_name.data + " " + form.last_name.data, form.cell.data, form.email.data)
            account_id = account.add()
            user_id = User.add(form.email.data, form.first_name.data, form.last_name.data, \
                account_id, 'realtor', form.cell.data, form.password.data, confirmed=True)

            login_user(User(str(user_id),form.email.data,account_id,superuser=False,active=True))

            # Add default app template and app template steps to new users
            app_templates = AppTemplate.all()
            app_templates_count = app_templates.count(True)
            for app_template in app_templates:
                # get the app template steps
                app_template_steps = AppTemplateStep.all(app_template['_id'])

                # create the template in the account
                template = Template(app_template['name'], account_id)
                template_id = template.add()

                # create each template step in the new account template
                for app_template_step in app_template_steps:
                    days_before_close = app_template_step['steps']['days_before_close'] if 'days_before_close' in app_template_step['steps'] else None
                    name = app_template_step['steps']['name'] if 'name' in app_template_step['steps'] else None
                    notes = app_template_step['steps']['notes'] if 'notes' in app_template_step['steps'] else None

                    template_step = TemplateStep(template_id, name, notes, days_before_close)
                    template_step.add()

            flash("Welcome and we added %s templates to get you started" % (app_templates_count), category='success')
            return redirect(url_for('listing.listings'))
        else:
            flash("User already exists", category='danger')
    else:
        flash_errors(form)
    return render_template('account/register.html', form=form)

@account.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST':
        user = User.get(email=form.email.data)
        if user and User.validate_login(user['password'], form.password.data):
            user_obj = User(str(user['_id']),user['email'],user['account'],user['superuser'],user['active'])
            if user_obj.is_active() is True:
                login_user(user_obj, remember=form.remember_me.data)
                User.log_login(user_obj)
                flash("Logged in successfully", category='success')
                return redirect(url_for('listing.listings'))
            else:
                flash("Wrong email or password", category='danger')
        else:
            flash("Wrong email or password", category='danger')
    return render_template('account/login.html', title='login', form=form)

@account.route('/impersonate', methods=['GET', 'POST'])
def impersonate():
    form = ImpersonateForm()

    if request.method == 'POST':
        user = User.get(email=form.email.data)
        if user and User.validate_login(user['password'], form.password.data) and user['superuser']:
            impersonate_user = User.get(email=form.impersonate_email.data)
            if impersonate_user:
                user_obj = User(str(impersonate_user['_id']),impersonate_user['email'],impersonate_user['account'],impersonate_user['superuser'],impersonate_user['active'])
                if user_obj.is_active() is True:
                    login_user(user_obj)
                    flash("Logged in successfully", category='success')
                    return redirect(url_for('listing.listings'))
                else:
                    flash("Wrong email or password", category='danger')
            else:
                flash("User doesn't exist", category='danger')
        else:
            flash("Wrong email or password", category='danger')
    return render_template('account/impersonate.html', title='login', form=form)

@account.route('/logout')
def logout():
    logout_user()
    flash("Logged out successfully", category='success')
    return redirect(url_for('home.homepage'))

### Templates ###

@account.route('/templates')
@login_required
@admin_login_required
def templates():
    templates = Template.all(current_user.get_account())
    count = templates.count(True)
    return render_template('account/templates.html', templates=templates, count=count)

@account.route('/templates/add', methods=['GET', 'POST'])
@login_required
@admin_login_required
def add_template():
    form = TemplateForm()
    if request.method == 'POST' and form.validate_on_submit():
        template = Template(form.name.data, current_user.get_account())
        id = template.add()
        return redirect(url_for('account.template_steps', id=id))
    else:
        flash_errors(form)
    return render_template('account/template.html', template=[], form=form)


@account.route('/templates/edit/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_template(id):
    form = TemplateForm()

    if request.method == 'GET':
        template = Template.get(id)
        form.name.data = template['name']

    if request.method == 'POST' and form.validate_on_submit():
        Template.update(id, form.name.data)
        return redirect(url_for('account.templates'))
    else:
        flash_errors(form)
    return render_template('account/template.html', id=id, template=template, form=form)


@account.route('/templates/delete/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def delete_template(id):
    Template.delete(id)
    flash("Template removed succesfully", category='success')
    return redirect(url_for('account.templates'))


### Template Steps ###

@account.route('/templates/<string:id>/steps', methods=['GET', 'POST'])
@login_required
@admin_login_required
def template_steps(id):
    template = Template.get(id)
    template_steps = TemplateStep.all(id)
    # this is weird but I had to get the cursor twice
    # because whenever I used "list" it would replace my template_steps_list
    # even when I just was referencing the variable
    template_steps_list = TemplateStep.all(id)
    count = len(list(template_steps_list))

    # this is edit template but we're doing it in a modal since it's just a name
    form = TemplateForm()

    if request.method == 'GET':
        form.name.data = template['name']

    if request.method == 'POST' and form.validate_on_submit():
        Template.update(id, form.name.data)
        return redirect(url_for('account.template_steps', id=id))
    else:
        flash_errors(form)

    return render_template('account/templatesteps.html', form=form, id=id, template=template, template_steps=template_steps, count=count)

@account.route('/templates/<string:id>/steps/add', methods=['GET', 'POST'])
@login_required
@admin_login_required
def add_template_step(id):
    form = TemplateStepForm()
    if request.method == 'POST' and form.validate_on_submit():
        template_step = TemplateStep(id, form.name.data, form.notes.data, form.days_before_close.data)
        template_step.add()
        return redirect(url_for('account.template_steps', id=id))
    else:
        flash_errors(form)
    return render_template('account/templatestep.html', id=id, template_step=[], form=form)

@account.route('/templates/<string:id>/steps/edit/<string:step_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_template_step(id, step_id):
    form = TemplateStepForm()

    if request.method == 'GET':
        template_step = TemplateStep.get(id, step_id)
        form.name.data = template_step['steps'][0]['name']
        form.notes.data = template_step['steps'][0]['notes']
        form.days_before_close.data = template_step['steps'][0]['days_before_close'] if 'days_before_close' in template_step['steps'][0] else None
        return render_template('account/templatestep.html', id=id, step_id=step_id, template_step=template_step, form=form)

    if request.method == 'POST' and form.validate_on_submit():
        TemplateStep.update(id, step_id, form.name.data, form.notes.data, form.days_before_close.data)
        return redirect(url_for('account.template_steps', id=id))
    else:
        flash_errors(form)
        return render_template('account/templatestep.html', id=id, step_id=step_id, template_step=[], form=form)

@account.route('/templates/<string:id>/steps/delete/<string:step_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def delete_template_step(id, step_id):
    TemplateStep.delete(id, step_id)
    flash("Step removed succesfully", category='success')
    return redirect(url_for('account.template_steps', id=id))

@account.route('/templates/<string:id>/steps/sort', methods=['POST'])
@login_required
def sort_template_step(id):
    TemplateStep.sort(id, request.form['order'])
    return json.dumps({'status':'Successfully sorted'})


### My Account ###

@account.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    form = UserForm()
    user = User.get(current_user.get_id())
    role = user['role']

    if request.method == 'GET':
        form.first_name.data = user['first_name']
        form.last_name.data = user['last_name']
        form.email.data = user['email']
        form.cell.data = user['cell']
        form.email_alert.data = user['email_alert'] if 'email_alert' in user else True
        form.text_alert.data = user['text_alert'] if 'text_alert' in user else True

    if request.method == 'POST' and form.validate_on_submit():
        id = current_user.get_id()
        fn = form.first_name.data
        ln = form.last_name.data
        e = form.email.data
        c = form.cell.data
        p = None # don't want to set the password as we don't have it on page; model handles
        ea = form.email_alert.data
        ta = form.text_alert.data
        User.update(id=id, email=e, first_name=fn, last_name=ln, cell=c, password=p, \
            confirmed=True, email_alert=ea, text_alert=ta)
        flash("Updated successfully", category='success')
        return redirect(url_for('listing.listings'))
    else:
        flash_errors(form)

    return render_template('account/user.html', form=form, role=role)

@account.route('/password', methods=['GET', 'POST'])
@login_required
def password():
    form = PasswordForm()
    user = User.get(current_user.get_id())
    role = user['role']

    if request.method == 'GET':
        form.password.data = user['password']

    if request.method == 'POST' and form.validate_on_submit():
        id = current_user.get_id()
        fn = user['first_name']
        ln = user['last_name']
        e = user['email']
        c = user['cell']
        p = form.password.data
        ea = user['email_alert']
        ta = user['text_alert']
        User.update(id=id, email=e, first_name=fn, last_name=ln, cell=c, password=p, \
            email_alert=ea, text_alert=ta)
        flash("Updated successfully", category='success')
        return redirect(url_for('listing.listings'))
    else:
        flash_errors(form)

    return render_template('account/password.html', form=form)

### Team admins ###

'''https://github.com/allisson/flask-example/blob/master/accounts/views.py'''

@account.route('/admins')
@login_required
@admin_login_required
def admins():
    users = User.all(account=current_user.get_account())
    count = users.count(True)
    return render_template('account/admins.html', users=users, count=count, title="Welcome")


@account.route('/admins/invite', methods=['GET', 'POST'])
@login_required
@admin_login_required
def invite_admin():
    form = InviteForm()

    if request.method == 'GET':
        return render_template('account/admin.html', user=[], form=form)

    if request.method == 'POST' and form.validate_on_submit():
        existing_user = User.get(email=form.email.data)
        if existing_user is None:
            try:
                send_invitation(form.email.data)
                User.add(form.email.data, form.first_name.data, form.last_name.data, \
                    current_user.get_account(), 'admin', invited_by=current_user.get_id(), confirmed=False)
                flash("Invitation sent", category='success')
            except:
                flash("Error inviting team member", category='danger')
                return render_template('account/admin.html', form=form)

            return redirect(url_for('account.admins'))
        else:
            flash("User already exists", category='danger')
            return render_template('account/admin.html', user=[], form=form)
    else:
        flash_errors(form)
        return render_template('account/admin.html', user=[], form=form)

###### page user visits to confirm the link from their email ######
@account.route('/register/<token>', methods=['GET', 'POST'])
def register_with_token(token):
    form = RegForm()

    if request.method == 'GET':
        try:
            email = confirm_token(token)
            user = User.get(email=email)

            if user['confirmed']:
                flash('Account already confirmed. Please login.', 'success')
                return redirect(url_for('account.login'))
            else:
                form.email.data = email
                return render_template('account/register.html', form=form)
        except:
            flash('The confirmation link is invalid or has expired.', 'danger')
            return redirect(url_for('account.login'))

    if request.method == 'POST' and form.validate_on_submit():
        user = User.get(email=form.email.data)

        id = user['_id']
        account_id = user['account']
        fn = form.first_name.data
        ln = form.last_name.data
        e = form.email.data
        c = form.cell.data
        p = form.password.data
        ea = True if user['role'] == 'client' else False
        ta = True if user['role'] == 'client' else False

        User.update(id=id, email=e, first_name=fn, last_name=ln, cell=c, password=p, confirmed=True, \
            email_alert=ea, text_alert=ta)
        login_user(User(str(id),form.email.data,account_id,superuser=False, active=True))
        flash("Updated successfully", category='success')
        return redirect(url_for('listing.listings'))
    else:
        flash_errors(form)

@account.route('/admins/edit/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_admin(id):
    form = InviteForm()

    if request.method == 'GET':
        user = User.get(id)
        form.first_name.data = user['first_name']
        form.last_name.data = user['last_name']
        form.email.data = user['email']

        return render_template('account/admin.html', id=id, user=user, form=form)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            User.update(id, form.email.data, form.first_name.data, form.last_name.data)
            send_invitation(form.email.data)
            flash("Invitation resent", category='success')
        except:
            flash("Error inviting team member", category='danger')
            return render_template('account/admin.html', form=form)

        return redirect(url_for('account.admins'))
    else:
        flash_errors(form)


@account.route('/admins/delete/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def delete_admin(id):
    User.delete(id=id, context='admin')
    flash("User removed succesfully", category='success')
    return redirect(url_for('account.admins'))

###### page user visits to request forgotten password ######
@account.route('/forgotpassword', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()

    if request.method == 'GET':
        return render_template('account/forgotpassword.html', form=form)

    if request.method == 'POST' and form.validate_on_submit():
        existing_user = User.get(email=form.email.data)
        if existing_user:
            try:
                send_reset(form.email.data)
                flash("Please check your email to reset your password", category='success')
                return redirect(url_for('account.login'))
            except:
                flash("Error sending password reset", category='danger')
                return render_template('account/forgotpassword.html', form=form)
        else:
            flash("Email address doesn't exist", category='danger')
            return render_template('account/forgotpassword.html', form=form)
    else:
        flash_errors(form)


###### page user visits to reset their password ######
@account.route('/resetpassword/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm()

    email = confirm_token(token)
    user = User.get(email=email)

    if request.method == 'GET':
        try:
            if user:
                return render_template('account/resetpassword.html', form=form)
            else:
                flash('The confirmation link is invalid or has expired.', 'danger')
                return redirect(url_for('account.login'))
        except:
            flash('The confirmation link is invalid or has expired.', 'danger')
            return redirect(url_for('account.login'))

    if request.method == 'POST' and form.validate_on_submit():
        id = user['_id']
        first_name = user['first_name']
        last_name = user['last_name']
        email = user['email']
        p = form.password.data

        User.update(id=id, email=email, first_name=first_name, last_name=last_name, password=p)
        flash("Updated successfully.  Login below.", category='success')
        return redirect(url_for('account.login'))
    else:
        flash_errors(form)
