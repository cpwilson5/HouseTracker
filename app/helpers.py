from flask import flash, url_for
from flask import current_app as app
from itsdangerous import URLSafeSerializer
from .utils import send_email
import re
import os

def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"%s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')

### Email confirmation ###
'''https://realpython.com/handling-email-confirmation-in-flask/#add-email-confirmation'''

def send_invitation(email, realtor, new_user=True):
    if new_user:
        token = generate_confirmation_token(email)
        confirm_url = url_for('account.register_with_token', token=token, _external=True)
        html = "You can now track and see updates about your house listing in real-time!<br><br>Join by clicking here: " + confirm_url
        subject = "You've been invited by %s %s" % (realtor['first_name'],realtor['last_name'])
    else:
        html = "View your new listing by logging in here: " + url_for('account.login', _external=True)
        subject = "You've been added to another listing by %s %s" % (realtor['first_name'],realtor['last_name'])

    send_email([email], subject, html)

def send_reset(email):
    token = generate_confirmation_token(email)
    confirm_url = url_for('account.reset_password', token=token, _external=True)
    html = "Reset your password: " + confirm_url
    subject = "Reset your password"
    send_email([email], subject, html)

def generate_confirmation_token(email):
    serializer = URLSafeSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['MAIL_SECURITY_PASSWORD_SALT'])

def confirm_token(token):
    serializer = URLSafeSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['MAIL_SECURITY_PASSWORD_SALT'],
        )
    except:
        return False
    return email

# pretty_date in template/html
# def pretty_date(value): --> see listing init.py file

# pretty_date in view
def pretty_date(date_time):
    if date_time.hour != 0 or date_time.minute != 0:
        return date_time.strftime('%m/%d/%Y %-I:%M %p')
    else:
        return date_time.strftime('%m/%d/%Y')

def distro(users, type):
    distro = []

    for user in users:
        if type == 'cell':
            cell_number = user[type].encode("utf-8") #convert unicode to string
            value = re.sub(b'[^0-9]', '', cell_number) #strip out non-numerics
        else:
            value = user[type]

        distro.append(value)

    return distro
