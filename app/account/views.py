from flask import render_template
from flask_login import login_user, logout_user, login_required, current_user
from flask import request, redirect, render_template, url_for, flash, current_app
from .forms import StepForm, UserForm, InviteForm, RegForm, LoginForm
from models import User, Account, Step
from ..configuration.models import AppStep
from ..helpers import flash_errors, confirm_token, send_invitation

from . import account

@account.route('/register', methods=['GET', 'POST'])
def register():
    form = RegForm()

    if request.method == 'POST' and form.validate_on_submit():
        existing_user = User.get(email=form.email.data)
        if existing_user is None:
            account = Account('namevalue', 'phonevalue', 'emailvalue')
            account_id = account.add()
            user_id = User.add(form.first_name.data, form.last_name.data, form.email.data, \
                account_id, 'realtor', form.cell.data, form.password.data, confirmed=True)

            login_user(User(str(user_id),form.email.data,account_id,superuser=False,active=True))

            # Add default app steps to new users
            app_steps = AppStep.all()
            app_steps_count = app_steps.count(True)
            for app_step in app_steps:
                step = Step(app_step['name'], app_step['notes'], account_id)
                step.add()
            flash("Welcome and we added %s steps to get you started" % (app_steps_count), category='success')
            return redirect(url_for('home.dashboard'))
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
                flash("Logged in successfully", category='success')
                return redirect(url_for('listing.listings'))
            else:
                flash("Wrong email or password", category='danger')
        else:
            flash("Wrong email or password", category='danger')
    return render_template('account/login.html', title='login', form=form)

@account.route('/logout')
def logout():
    logout_user()
    flash("Logged out successfully", category='success')
    return redirect(url_for('home.homepage'))

### Steps ###

@account.route('/steps')
@login_required
def steps():
    steps = Step.all(current_user.get_account())
    return render_template('account/steps.html', steps=steps, title="Welcome")

@account.route('/steps/add', methods=['GET', 'POST'])
@login_required
def add_step():
    form = StepForm()
    if request.method == 'POST' and form.validate_on_submit():
        step = Step(form.name.data, form.notes.data, current_user.get_account())
        step.add()
        return redirect(url_for('account.steps'))
    else:
        flash_errors(form)
    return render_template('account/step.html', form=form)


@account.route('/steps/edit/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_step(id):
    form = StepForm()

    if request.method == 'GET':
        step = Step.get(id)
        form.name.data = step['name']
        form.notes.data = step['notes']

    if request.method == 'POST' and form.validate_on_submit():
        Step.update(id, form.name.data, form.notes.data)
        return redirect(url_for('account.steps'))
    else:
        flash_errors(form)
    return render_template('account/step.html', form=form)


@account.route('/steps/delete/<string:id>', methods=['GET', 'POST'])
@login_required
def delete_step(id):
    Step.delete(id)
    flash("Step removed succesfully", category='success')
    return redirect(url_for('account.steps'))

### My Account ###

@account.route('/user', methods=['GET', 'POST'])
def user():
    form = UserForm()

    if request.method == 'GET':
        user = User.get(current_user.get_id())
        form.first_name.data = user['firstname']
        form.last_name.data = user['lastname']
        form.email.data = user['email']
        form.cell.data = user['cell']
        form.password.data = user['password']

    if request.method == 'POST' and form.validate_on_submit():
        id = current_user.get_id()
        fn = form.first_name.data
        ln = form.last_name.data
        e = form.email.data
        c = form.cell.data
        p = form.password.data
        User.update(id=id, first_name=fn, last_name=ln, email=e, cell=c, password=p)
        flash("Updated successfully", category='success')
        return redirect(url_for('home.dashboard'))
    else:
        flash_errors(form)
    return render_template('account/account.html', form=form)

### Team admins ###

'''https://github.com/allisson/flask-example/blob/master/accounts/views.py'''

@account.route('/admins')
@login_required
def admins():
    users = User.all(account=current_user.get_account())
    return render_template('account/admins.html', users=users, title="Welcome")


@account.route('/admins/invite', methods=['GET', 'POST'])
@login_required
def invite_admin():
    form = InviteForm()

    if request.method == 'GET':
        return render_template('account/admin.html', form=form)

    if request.method == 'POST' and form.validate_on_submit():
        existing_user = User.get(email=form.email.data)
        if existing_user is None:
            try:
                send_invitation(form.email.data)
                User.add(form.first_name.data, form.last_name.data, form.email.data, \
                    current_user.get_account(), 'admin', invited_by=current_user.get_id(), confirmed=False)
                flash("Invitation sent", category='success')
            except:
                flash("Error inviting team member", category='danger')
                return render_template('account/admin.html', form=form)

            return redirect(url_for('account.admins'))
        else:
            flash("User already exists", category='danger')
            return render_template('account/admin.html', form=form)
    else:
        flash_errors(form)

### resend invite ###
@account.route('/admins/invite/retry/<string:email>', methods=['GET'])
@login_required
def retry_invite_admin(email):
    try:
        send_invitation(email)
        flash("Invitation sent", category='success')
    except:
        flash("Error attempting to resend invite", category='danger')
        return render_template('account/admin.html', form=form)
    return redirect(url_for('account.admins'))

###### page user visits to confirm the link from their email ######
@account.route('/register/<token>', methods=['GET', 'POST'])
def register_admin(token):
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

        User.update(id=id, first_name=fn, last_name=ln, email=e, cell=c, password=p, confirmed=True)
        login_user(User(str(id),form.email.data,account_id,superuser=False, active=True))
        flash("Updated successfully", category='success')
        return redirect(url_for('home.dashboard'))
    else:
        flash_errors(form)

@account.route('/admins/edit/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_admin(id):
    form = InviteForm()

    if request.method == 'GET':
        user = User.get(id)
        form.first_name.data = user['firstname']
        form.last_name.data = user['lastname']
        form.email.data = user['email']

    if request.method == 'POST' and form.validate_on_submit():
        try:
            User.update(id, form.first_name.data, form.last_name.data, form.email.data)
            send_invitation(form.email.data)
            flash("Invitation resent", category='success')
        except:
            flash("Error inviting team member", category='danger')
            return render_template('account/admin.html', form=form)

        return redirect(url_for('account.admins'))
    else:
        flash_errors(form)
    return render_template('account/admin.html', form=form)

@account.route('/admins/delete/<string:id>', methods=['GET', 'POST'])
@login_required
def delete_admin(id):
    User.delete(id=id)
    flash("User removed succesfully", category='success')
    return redirect(url_for('account.admins'))
