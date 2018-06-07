from flask import render_template
from flask_login import login_required, current_user
from flask import request, redirect, render_template, url_for, flash, current_app as app
from flask_pymongo import PyMongo
from .forms import ListingForm, ListingStepForm
from ..account.forms import InviteForm
from models import Listing, ListingStep
from ..account.models import User, Step
from bson import ObjectId
from ..utils import s3_upload, s3_retrieve, send_sms
from ..helpers import flash_errors, confirm_token, send_invitation
from datetime import datetime
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
        listing = Listing(form.name.data, form.address1.data, \
        form.address2.data, form.city.data, form.state.data, form.zip.data, \
        form.close_date.data)
        listing_id = listing.add()

        # Add user's steps to new listing
        steps = Step.all(current_user.get_account())
        steps_count = steps.count(True)
        for step in steps:
            listing_step = ListingStep(listing_id, step['name'], step['notes'])
            listing_step.add()
        flash("Successfully created %s with %s steps" % (form.name.data, steps_count), category='success')
        return redirect(url_for('listing.listings'))
    else:
        flash_errors(form)
    return render_template('listing/listing.html', form=form)

@listing.route('/listings/edit/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_listing(id):
    form = ListingForm()

    if request.method == 'GET':
        listing = Listing.get(id)
        form.name.data = listing['name']
        form.address1.data = listing['address1']
        form.address2.data = listing['address2']
        form.city.data = listing['city']
        form.state.data = listing['state']
        form.zip.data = listing['zip']
        form.close_date.data = datetime.strptime(listing['close_date'], '%Y-%m-%dT%H:%M:%S') if 'close_date' in listing else None

    if request.method == 'POST' and form.validate_on_submit():
        Listing.update(id, form.name.data, form.address1.data, \
        form.address2.data, form.city.data, form.state.data, form.zip.data, \
        form.close_date.data)
        return redirect(url_for('listing.listings'))
    else:
        flash_errors(form)
    return render_template('listing/listing.html', id=id, form=form)

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
    return render_template('listing/listingsteps.html', id=id, listing_steps=listing_steps, users=users, listing=listing, title="Welcome")

@listing.route('/listings/<string:id>/steps/add', methods=['GET', 'POST'])
@login_required
def add_listing_step(id):
    form = ListingStepForm()
    if request.method == 'POST' and form.validate_on_submit():
        if form.attachment.data:
            s3_filepath = s3_upload(form.attachment)
        else:
            s3_filepath = None

        listing_step = ListingStep(listing_id=id, name=form.name.data, \
        notes=form.notes.data, attachment=s3_filepath, due_date=form.due_date.data, \
        color = form.color.data)
        listing_step.add()
        #send_sms('+15407466097', 'Step Added:  Details go here')

        flash("Successfully added listing step", category='success')
        return redirect(url_for('listing.listing_steps', id=id))
    else:
        flash_errors(form)
    return render_template('listing/listingstep.html', form=form)

@listing.route('/listings/<string:id>/steps/edit/<string:step_id>', methods=['GET', 'POST'])
@login_required
def edit_listing_step(id, step_id):
    form = ListingStepForm()

    if request.method == 'GET':
        listing_step = ListingStep.get(id, step_id)
        form.name.data = listing_step['steps'][0]['name']
        form.notes.data = listing_step['steps'][0]['notes']
        form.due_date.data = listing_step['steps'][0]['duedate']
        form.color.data = listing_step['steps'][0]['color'] if 'color' in listing_step['steps'][0] else 'Green'
        attachment = listing_step['steps'][0]['attachment']
        return render_template('listing/listingstep.html', form=form, attachment=attachment, id=id, step_id=step_id)

    if request.method == 'POST' and form.validate_on_submit():
        if form.attachment.data:
            s3_filepath = s3_upload(form.attachment)
        else:
            s3_filepath = None

        ListingStep.update(id=id, step_id=step_id, name=form.name.data, \
        notes=form.notes.data, attachment=s3_filepath, due_date=form.due_date.data, \
        color=form.color.data)

        return redirect(url_for('listing.listing_steps', id=id))
    else:
        flash_errors(form)
        return redirect(url_for('listing.edit_listing_step', id=id, step_id=step_id))


@listing.route('/attachment/<string:attachment>', methods=['GET'])
@login_required
def get_attachment(attachment):
    return redirect(s3_retrieve(attachment))

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
        form.first_name.data = user['firstname']
        form.last_name.data = user['lastname']
        form.email.data = user['email']

        return render_template('listing/client.html', id=id, user=user, form=form)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            User.update(client_id, form.first_name.data, form.last_name.data, form.email.data)
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
