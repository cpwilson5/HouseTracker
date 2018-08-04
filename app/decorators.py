from flask import request, redirect, render_template, url_for, flash, current_app as app
from functools import wraps
from flask_login import current_user
import re

def admin_login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # we only need to do this if they are a client (aka not a realtor or admin)
        ####if current_user.get_role() == 'client':
            ####clients_listing = current_user.get_listing()[0] #currently a client can only have 1 listing
            # if it's the listing steps route then they should only have access to their listing
            # if they are already on their listing then we don't want to put them into an infinite loop
            ####if bool(re.match('/listings/(.*)/steps$', request.path)):
                ####requested_listing = kwargs['id'] #comes through automatically in decorator

                # if the client is trying to get to a listing that's not theirs, let's redirect them
                ####if clients_listing != requested_listing:
                    ####return redirect(url_for('listing.listing_steps', id=clients_listing))
            # if it's not the listing steps route then they shouldn't have access
            ####else:
                ####return redirect(url_for('listing.listing_steps', id=clients_listing))
        return func(*args, **kwargs)
    return decorated_function
