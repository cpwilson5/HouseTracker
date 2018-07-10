# third-party imports
from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_mail import Mail, Message


# local imports
from config import app_config

# db variable initialization
login_manager = LoginManager()
mail = Mail()

def create_app(config_name):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')


    mail.init_app(app)

    login_manager.init_app(app)
    login_manager.login_message = "You must be logged in to access this page."
    login_manager.login_message_category = "danger"
    login_manager.login_view = "account.login"

    from app import models

    from .home import home as home_blueprint
    app.register_blueprint(home_blueprint)

    from .account import account as account_blueprint
    app.register_blueprint(account_blueprint)

    from .configuration import configuration as configuration_blueprint
    app.register_blueprint(configuration_blueprint)

    from .listing import listing as listing_blueprint
    app.register_blueprint(listing_blueprint)

    return app
