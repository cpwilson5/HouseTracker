from flask import render_template
from flask_login import login_required, current_user
from flask import request, redirect, render_template, url_for, flash, current_app as app
from flask_pymongo import PyMongo
from .forms import ListingForm, ListingStepForm, InfoForm
from ..account.forms import InviteForm
from .models import Listing, ListingStep
from ..account.models import User, Template, TemplateStep, Account
from bson import ObjectId
from ..utils import s3_upload, s3_retrieve, send_sms, send_email
from ..helpers import flash_errors, confirm_token, send_invitation, distro, pretty_date
from ..decorators import admin_login_required
import datetime
import json

from . import listing

@listing.route('/listings')
@login_required
@admin_login_required
def listings():

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

    listings = Listing.all(active=True, complete=complete, sort=sort, order=order)
    return render_template('listing/listings.html', listings=listings, title="Welcome")

@listing.route('/listings/add', methods=['GET', 'POST'])
@login_required
@admin_login_required
def add_listing():
    form = ListingForm()
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

        listing = Listing(form.name.data, form.address1.data, \
        form.address2.data, form.city.data, form.state.data, form.zip.data, \
        date_time, photo=s3_filepath)
        listing_id = listing.add()

        # Add user's template steps to new listing
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
                due_date = None

            name = template_step['steps']['name'] if 'name' in template_step['steps'] else None
            notes = template_step['steps']['notes'] if 'notes' in template_step['steps'] else None

            listing_step = ListingStep(listing_id, name=name, notes=notes, due_date=due_date_time, status='red')
            listing_step.add()
        flash("Successfully created %s with %s steps" % (form.name.data, template_steps_count), category='success')
        return redirect(url_for('listing.listing_steps', id=listing_id))
    else:
        flash_errors(form)
    return render_template('listing/listing.html', form=form)

@listing.route('/listings/edit/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_listing(id):
    form = ListingForm()
    listing = Listing.get(id)

    if request.method == 'GET':
        form.name.data = listing['name']
        form.address1.data = listing['address1']
        form.address2.data = listing['address2']
        form.city.data = listing['city']
        form.state.data = listing['state']
        form.zip.data = listing['zip']
        form.close_date.data = listing['close_date'] if listing['close_date'] else None
        form.close_time.data = listing['close_date'] if listing['close_date'] and (listing['close_date'].hour != 0 and listing['close_date'] != 0) else None
        photo = listing['photo'] if 'photo' in listing else None

        return render_template('listing/listing.html', id=id, form=form, photo=photo)

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

        Listing.update(id, form.name.data, form.address1.data, \
        form.address2.data, form.city.data, form.state.data, form.zip.data, \
        date_time, photo=s3_filepath)

        # compare changes to provide details in text/email
        if listing['close_date']:
            db_close_date = listing['close_date'].replace(tzinfo=None)
        else:
            db_close_date = None

        if date_time != db_close_date and form.close_date.data:
            # build body of email/text based on what changed and email/text only if changes
            email_body = "You're closing date has been updated to " + pretty_date(date_time) + "<br><br>"
            text_body = "You're closing date has been updated to " + pretty_date(date_time) + ".\n\n"

            email_body = email_body + "<br>Login for more details: " + url_for('account.login', _external=True)
            text_body = text_body + "\nLogin here: " + url_for('account.login', _external=True)

            # then send email updates only if there are changes
            email_users = User.all(listing=id, email_alert=True)
            email_distro = distro(email_users, 'email')
            if email_distro:
                send_email(email_distro, "You're listing has been updated", email_body)

            # send text update
            text_users = User.all(listing=id, text_alert=True)
            text_distro = distro(text_users, 'cell')
            if text_distro:
                send_sms(text_distro, text_body)
        # otherwise don't send an email or text if closing date didn't change

        flash("Updated listing", category='success')
        return redirect(url_for('listing.listing_steps', id=id))
    else:
        flash_errors(form)
        return render_template('listing/listing.html', id=id, form=form)

@listing.route('/listings/<string:id>/info', methods=['GET', 'POST'])
@login_required
def edit_info(id):
    form = InfoForm()
    listing = Listing.get(id)

    if request.method == 'GET':
        form.info.data = listing['info'] if 'info' in listing else None

    if request.method == 'POST' and form.validate_on_submit():
        info = form.info.data
        Listing.info_update(id, info=info) ### this should be on a listing edit method in the model, not a new method
        flash("Updated listing", category='success')
        return redirect(url_for('listing.listing_steps', id=id))
    else:
        flash_errors(form)
    return render_template('listing/info.html', form=form)

@listing.route('/photo/<string:photo>', methods=['GET'])
@login_required
def get_photo(photo):
    return redirect(s3_retrieve(photo, 'photo'))

@listing.route('/listings/delete/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def delete_listing(id):
    Listing.delete(id)
    flash("Listing deleted", category='success')
    return redirect(url_for('listing.listings'))

@listing.route('/listings/complete/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def complete_listing(id):
    Listing.complete(id)
    flash("Congrats!  Your listing has been closed", category='success')
    return redirect(url_for('listing.listings'))

@listing.route('/listings/reactivate/<string:id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def reactivate_listing(id):
    Listing.reactivate(id)
    flash("Listing has been reactivated", category='success')
    return redirect(url_for('listing.listings'))

@listing.route('/listings/<string:id>/steps')
@login_required
@admin_login_required
def listing_steps(id):
    listing_steps = list(ListingStep.all(id, active=True, complete=False))
    if not listing_steps:
        listing_steps = []
    users = User.all(listing=id)
    listing = Listing.get(id)
    realtor = User.get(accounts_realtor=current_user.get_account())

    if listing['close_date']:
        days_left = (listing['close_date'].replace(tzinfo=None) - datetime.datetime.now()).days
        if days_left < 0:
            days_left = 0
    else:
        days_left = "TBD"
    return render_template('listing/listingsteps.html', id=id, listing_steps=listing_steps, users=users, listing=listing, realtor=realtor, days_left=days_left, title="Welcome")

@listing.route('/listings/<string:id>/steps/add', methods=['GET', 'POST'])
@login_required
@admin_login_required
def add_listing_step(id):
    form = ListingStepForm()
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

        listing_step = ListingStep(listing_id=id, name=form.name.data, \
        notes=form.notes.data, attachment=s3_filepath, due_date=date_time, \
        status = form.status.data)
        listing_step.add()

        # build body of email/text
        email_body = "A listing step '" + form.name.data + "' has been added.<br><br>"
        text_body = "A listing step '" + form.name.data + "' has been added.\n\n"

        if date_time:
            email_body = email_body + "Scheduled Date: " + pretty_date(date_time) + "<br>"
            text_body = text_body + "Scheduled Date: " + pretty_date(date_time) + "\n"
        if s3_filepath:
            email_body = email_body + "Attachment: Added<br>"
            text_body = text_body + "Attachment: Added\n"

        email_body = email_body + "<br>Login for more details: " + url_for('account.login', _external=True)
        text_body = text_body + "\nLogin here: " + url_for('account.login', _external=True)

        # then send email updates only if there are changes
        email_users = User.all(listing=id, email_alert=True)
        email_distro = distro(email_users, 'email')
        if email_distro:
            send_email(email_distro, "You're listing has been updated", email_body)

        # send text update
        text_users = User.all(listing=id, text_alert=True)
        text_distro = distro(text_users, 'cell')
        if text_distro:
            send_sms(text_distro, text_body)

        flash("Successfully added listing step", category='success')
        return redirect(url_for('listing.listing_steps', id=id))
    else:
        flash_errors(form)
    return render_template('listing/listingstep.html', form=form)

@listing.route('/listings/<string:id>/steps/edit/<string:step_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_listing_step(id, step_id):
    form = ListingStepForm()
    listing_step = ListingStep.get(id, step_id)

    if request.method == 'GET':
        form.name.data = listing_step['steps'][0]['name']
        form.notes.data = listing_step['steps'][0]['notes']
        form.due_date.data = listing_step['steps'][0]['due_date'] if listing_step['steps'][0]['due_date'] else None
        form.time.data = listing_step['steps'][0]['due_date'] if listing_step['steps'][0]['due_date'] and (listing_step['steps'][0]['due_date'].hour != 0 and listing_step['steps'][0]['due_date'] != 0) else None
        form.status.data = listing_step['steps'][0]['status'] if 'status' in listing_step['steps'][0] else 'Red'
        attachment = listing_step['steps'][0]['attachment']

        return render_template('listing/listingstep.html', form=form, attachment=attachment, id=id, step_id=step_id)

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

        # update listing step
        ListingStep.update(id=id, step_id=step_id, name=form.name.data, \
        notes=form.notes.data, attachment=s3_filepath, due_date=date_time, \
        status=form.status.data)

        # compare changes to provide details in text/email
        name_changed = False if form.name.data == listing_step['steps'][0]['name'] else True
        notes_changed = False if form.notes.data == listing_step['steps'][0]['notes'] else True
        status_changed = False if form.status.data == listing_step['steps'][0]['status'] else True
        attachment_changed = False if not s3_filepath else True

        # 5 scenarios for dates
            #1 same date to same date - don't send
            #2 date existed to new date - send
            #3 date existed to no date - don't send
            #4 no date to new date - send
            #5 no date to no date - don't send

        # check if an old date existed
        # setting to variable makes it cleaner to read
        if listing_step['steps'][0]['due_date']:
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
            if date_time == listing_step['steps'][0]['due_date'].replace(tzinfo=None):
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
                email_body = "You're listing step \'" + listing_step['steps'][0]['name'] + \
                    "\' has been updated to '" + form.name.data + "\'.<br><br>"
                text_body = "A listing step '" + form.name.data + "' has been updated.\n\n"
            else:
                email_body = "You're listing step '" + form.name.data + "' has been updated.<br><br>"
                text_body = "A listing step '" + form.name.data + "' has been updated.\n\n"

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
            email_users = User.all(listing=id, email_alert=True)
            email_distro = distro(email_users, 'email')
            if email_distro:
                send_email(email_distro, "You're listing has been updated", email_body)

            # send text update
            text_users = User.all(listing=id, text_alert=True)
            text_distro = distro(text_users, 'cell')
            if text_distro:
                send_sms(text_distro, text_body)
        # otherwise don't send an email or text if nothing changed

        return redirect(url_for('listing.listing_steps', id=id))
    else:
        flash_errors(form)
        return redirect(url_for('listing.edit_listing_step', id=id, step_id=step_id))


@listing.route('/attachment/<string:attachment>', methods=['GET'])
@login_required
def get_attachment(attachment):
    return redirect(s3_retrieve(attachment, 'attachment'))

@listing.route('/listings/<string:id>/steps/delete/<string:step_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def delete_listing_step(id, step_id):
    ListingStep.delete(id, step_id)
    return redirect(url_for('listing.listing_steps', id=id))

@listing.route('/listings/<string:id>/steps/complete/<string:step_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def complete_listing_step(id, step_id):
    ListingStep.complete(id, step_id)
    return redirect(url_for('listing.listing_steps', id=id))

@listing.route('/listings/<string:id>/steps/sort', methods=['POST'])
@login_required
def sort_listing_step(id):
    ListingStep.sort(id, request.form['order'])
    return json.dumps({'status':'Successfully sorted'})

### adding a listing user/client ###
@listing.route('/listings/<string:id>/clients/invite', methods=['GET', 'POST'])
@login_required
def invite_client(id):
    form = InviteForm()

    if request.method == 'GET':
        return render_template('listing/client.html', id=id, user=[], form=form)

    if request.method == 'POST' and form.validate_on_submit():
        existing_user = User.get(email=form.email.data)
        if existing_user is None:
            try:
                send_invitation(form.email.data)
                User.add(form.first_name.data,form.last_name.data, form.email.data, \
                    current_user.get_account(), 'client', invited_by=current_user.get_id(), \
                    confirmed=False, listing=[id])
                flash("Invitation sent", category='success')
            except:
                flash("Error inviting client", category='danger')
                return render_template('listing/client.html', id=id, form=form)

            return redirect(url_for('listing.listing_steps', id=id))
        else:
            ###  NEED TO FIX THIS TO ADD A LISTING TO AN ARRAY FOR THE USER ###
            flash("User already exists", category='danger')
            return render_template('listing/client.html', id=id, user=[], form=form)
    else:
        flash_errors(form)
        return render_template('listing/client.html', id=id, user=[], form=form)

@listing.route('/listings/<string:id>/clients/edit/<string:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(id, client_id):
    form = InviteForm()

    if request.method == 'GET':
        user = User.get(id=client_id)
        form.first_name.data = user['first_name']
        form.last_name.data = user['last_name']
        form.email.data = user['email']
        form.cell.data = user['cell']

        return render_template('listing/client.html', id=id, user=user, form=form)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            User.update(client_id, form.first_name.data, form.last_name.data, form.email.data, form.cell.data)
            send_invitation(form.email.data)
            flash("Invitation resent", category='success')
        except:
            flash("Error inviting client", category='danger')
            return render_template('listing/client.html', form=form)

        return redirect(url_for('listing.listing_steps', id=id))
    else:
        flash_errors(form)

@listing.route('/listings/<string:id>/clients/delete/<string:client_id>', methods=['GET', 'POST'])
@login_required
def delete_client(id, client_id):
    User.delete(id=client_id)
    flash("User removed succesfully", category='success')
    return redirect(url_for('listing.listing_steps', id=id))

''' resend invite - don't think we need this now that we moved resend to edit
@listing.route('/listings/<string:id>/clients/invite/retry/<string:email>', methods=['GET'])
@login_required
@admin_login_required
def retry_invite_client(id, email):
    try:
        send_invitation(email)
        flash("Invitation sent", category='success')
    except:
        flash("Error attempting to resend invite", category='danger')
        return redirect(url_for('listing.listing_steps', id=id, form=form))
    return redirect(url_for('listing.listing_steps', id=id))
'''
