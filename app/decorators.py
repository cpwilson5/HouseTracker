from flask import request, redirect, render_template, url_for, flash, current_app as app
from functools import wraps
from flask_login import current_user

def admin_login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.get_role() != 'realtor' and current_user.get_role() != 'admin':
            flash("You don't have access to this page", category='danger')
            listing_id = current_user.get_listing()[0]
            print listing_id
            return redirect(url_for('listing.listing_steps', id=listing_id))
        return func(*args, **kwargs)

    return decorated_function
