from flask import render_template
from flask_login import login_required, current_user
from flask import request, redirect, render_template, url_for, flash, current_app as app
from flask_pymongo import PyMongo
from .forms import ListingForm, ListingStepForm
from ..account.forms import InviteForm
from models import Listing, ListingStep
from ..account.models import User, Step
from bson import ObjectId
from ..utils import s3_upload, s3_retrieve, send_sms, send_email
from ..helpers import flash_errors, confirm_token, send_invitation, distro
from datetime import datetime, timedelta
import json

from . import listing

@listing.route('/listings')
@login_required
def listings():

    if request.args.get('sort') == 'closing':
        sort = 'close_date'
        order = 1
    elif request.args.get('sort') == 'updated':
        sort = 'update_date'
        order = -1
    elif request.args.get('sort') == 'inactive':
        sort = 'update_date'
        order = 1
    else:
        sort = 'create_date'
        order = -1

    listings = Listing.all(active=True, complete=False, sort=sort, order=order)

    return render_template('listing/listings.html', listings=listings, title="Welcome")

@listing.route('/listings/add', methods=['GET', 'POST'])
@login_required
def add_listing():
    form = ListingForm()
    if request.method == 'POST' and form.validate_on_submit():
        if form.photo.data:
            s3_filepath = s3_upload(form.photo, 'photo')
        else:
            s3_filepath = None

        listing = Listing(form.name.data, form.address1.data, \
        form.address2.data, form.city.data, form.state.data, form.zip.data, \
        form.close_date.data, photo=form.photo.data)
        listing_id = listing.add()

        # Add user's steps to new listing
        steps = Step.all(current_user.get_account())
        steps_count = steps.count(True)
        for step in steps:
            if 'days_before_close' in step:
                days_before_close = step['days_before_close']
                due_date = form.close_date.data - timedelta(days=days_before_close) if days_before_close else None
            else:
                due_date = None

            listing_step = ListingStep(listing_id, step['name'], step['notes'], due_date=due_date)
            listing_step.add()
        flash("Successfully created %s with %s steps" % (form.name.data, steps_count), category='success')
        return redirect(url_for('listing.listing_steps', id=listing_id))
    else:
        flash_errors(form)
    return render_template('listing/listing.html', form=form)

@listing.route('/listings/edit/<string:id>', methods=['GET', 'POST'])
@login_required
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
        form.close_date.data = datetime.strptime(listing['close_date'], '%Y-%m-%dT%H:%M:%S') if 'close_date' in listing else None
        photo = listing['photo'] if 'photo' in listing else None

        return render_template('listing/listing.html', id=id, form=form, photo=photo)

    if request.method == 'POST' and form.validate_on_submit():
        if form.photo.data:
            s3_filepath = s3_upload(form.photo, 'photo')
        else:
            s3_filepath = None

        Listing.update(id, form.name.data, form.address1.data, \
        form.address2.data, form.city.data, form.state.data, form.zip.data, \
        form.close_date.data, photo=s3_filepath)

        # compare changes to provide details in text/email
        if form.close_date.data <> datetime.strptime(listing['close_date'], '%Y-%m-%dT%H:%M:%S').date():
            # build body of email/text based on what changed and email/text only if changes
            email_body = "You're closing date has been updated to " + form.close_date.data.strftime('%m/%d/%Y') + "<br><br>"
            text_body = "You're closing date has been updated to " + form.close_date.data.strftime('%m/%d/%Y') + ".\n\n"

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

@listing.route('/photo/<string:photo>', methods=['GET'])
@login_required
def get_photo(photo):
    return redirect(s3_retrieve(photo, 'photo'))

@listing.route('/listings/delete/<string:id>', methods=['GET', 'POST'])
@login_required
def delete_listing(id):
    Listing.delete(id)
    return redirect(url_for('listing.listings'))

@listing.route('/listings/complete/<string:id>', methods=['GET', 'POST'])
@login_required
def complete_listing(id):
    Listing.complete(id)
    return redirect(url_for('listing.listings'))

@listing.route('/listings/<string:id>/steps')
@login_required
def listing_steps(id):
    listing_steps = list(ListingStep.all(id, active=True, complete=False))
    if not listing_steps:
        listing_steps = []
    users = User.all(listing=id)
    listing = Listing.get(id)
    days_left = (datetime.strptime(listing['close_date'], '%Y-%m-%dT%H:%M:%S') - datetime.now()).days
    if days_left < 0:
        days_left = 0
    return render_template('listing/listingsteps.html', id=id, listing_steps=listing_steps, users=users, listing=listing, days_left=days_left, title="Welcome")

@listing.route('/listings/<string:id>/steps/add', methods=['GET', 'POST'])
@login_required
def add_listing_step(id):
    form = ListingStepForm()
    if request.method == 'POST' and form.validate_on_submit():
        if form.attachment.data:
            s3_filepath = s3_upload(form.attachment, 'attachment')
        else:
            s3_filepath = None

        listing_step = ListingStep(listing_id=id, name=form.name.data, \
        notes=form.notes.data, attachment=s3_filepath, due_date=form.due_date.data, \
        status = form.status.data)
        listing_step.add()

        # build body of email/text
        email_body = "A listing step '" + form.name.data + "' has been added.<br><br>"
        text_body = "A listing step '" + form.name.data + "' has been added.\n\n"

        if form.due_date.data:
            email_body = email_body + "Due Date: " + form.due_date.data.strftime('%m/%d/%Y') + "<br>"
            text_body = text_body + "Due Date: " + form.due_date.data.strftime('%m/%d/%Y') + "\n"
        if form.status.data:
            email_body = email_body + "Status: " + form.status.data.capitalize() + "<br>"
            text_body = text_body + "Status: " + form.status.data.capitalize() + "\n"
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
def edit_listing_step(id, step_id):
    form = ListingStepForm()
    listing_step = ListingStep.get(id, step_id)

    if request.method == 'GET':
        form.name.data = listing_step['steps'][0]['name']
        form.notes.data = listing_step['steps'][0]['notes']
        form.due_date.data = listing_step['steps'][0]['due_date']
        form.status.data = listing_step['steps'][0]['status'] if 'status' in listing_step['steps'][0] else 'Green'
        attachment = listing_step['steps'][0]['attachment']

        return render_template('listing/listingstep.html', form=form, attachment=attachment, id=id, step_id=step_id)

    if request.method == 'POST' and form.validate_on_submit():
        if form.attachment.data:
            s3_filepath = s3_upload(form.attachment, 'attachment')
        else:
            s3_filepath = None

        # update listing step
        ListingStep.update(id=id, step_id=step_id, name=form.name.data, \
        notes=form.notes.data, attachment=s3_filepath, due_date=form.due_date.data, \
        status=form.status.data)

        # compare changes to provide details in text/email
        name_changed = False if form.name.data == listing_step['steps'][0]['name'] else True
        notes_changed = False if form.notes.data == listing_step['steps'][0]['notes'] else True
        due_date_changed = False if form.due_date.data == listing_step['steps'][0]['due_date'].date() else True
        status_changed = False if form.status.data == listing_step['steps'][0]['status'] else True
        attachment_changed = False if not s3_filepath else True

        # build body of email/text based on what changed and email/text only if changes
        if notes_changed or due_date_changed or status_changed or attachment_changed:
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
                email_body = email_body + "Due Date: " + form.due_date.data.strftime('%m/%d/%Y') + "<br>"
                text_body = text_body + "Due Date: " + form.due_date.data.strftime('%m/%d/%Y') + "\n"
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
def delete_listing_step(id, step_id):
    ListingStep.delete(id, step_id)
    return redirect(url_for('listing.listing_steps', id=id))

@listing.route('/listings/<string:id>/steps/complete/<string:step_id>', methods=['GET', 'POST'])
@login_required
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
            return render_template('listing/client.html', id=id, form=form)
    else:
        flash_errors(form)

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
def retry_invite_client(id, email):
    try:
        send_invitation(email)
        flash("Invitation sent", category='success')
    except:
        flash("Error attempting to resend invite", category='danger')
        return redirect(url_for('listing.listing_steps', id=id, form=form))
    return redirect(url_for('listing.listing_steps', id=id))
'''
