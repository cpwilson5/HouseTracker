from uuid import uuid4
import boto
import os.path
from flask import current_app as app
from werkzeug.utils import secure_filename
from flask import Flask, request
from twilio import twiml
from twilio.rest import TwilioRestClient
from flask_mail import Message
from app import mail

def s3_upload(source_file, upload_dir=None, acl='public-read'):
    #uncomment if we start wanting to use folders
    #if upload_dir is None:
    #    upload_dir = app.config["S3_UPLOAD_DIRECTORY"]

    source_filename = secure_filename(source_file.data.filename)
    source_extension = os.path.splitext(source_filename)[1]

    destination_filename = uuid4().hex + source_extension

    # Connect to S3 and upload file.
    conn = boto.connect_s3(app.config["S3_KEY"], app.config["S3_SECRET"])
    b = conn.get_bucket(app.config["S3_BUCKET"])

    #uncomment if we want to start using folders
    #sml = b.new_key("/".join([upload_dir, destination_filename]))
    sml = b.new_key("/".join([destination_filename]))
    sml.set_contents_from_string(source_file.data.read())
    sml.set_acl(acl)

    return destination_filename

def s3_retrieve(key, upload_dir=None, acl='public-read'):
    # Connect to S3 and get file.
    conn = boto.connect_s3(app.config["S3_KEY"], app.config["S3_SECRET"])
    b = conn.get_bucket(app.config["S3_BUCKET"])

    sml = b.get_key(key)
    url = sml.generate_url(3600, query_auth=True, force_http=True)
    return url

''' https://github.com/allisson/flask-example/blob/master/application.py
    https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xi-email-support
'''

def send_email(recipients, subject, body):
    msg = Message(subject)
    msg.sender = "info@housestatus.com"
    msg.recipients = recipients
    msg.html = body
    mail.send(msg)

def send_sms(to_numbers, body):
    account_sid = app.config['TWILIO_ACCOUNT_SID']
    auth_token = app.config['TWILIO_AUTH_TOKEN']
    twilio_number = app.config['TWILIO_NUMBER']
    client = TwilioRestClient(account_sid, auth_token)
    for to_number in to_numbers:
        client.messages.create(to=to_number,from_=twilio_number,body=body)
