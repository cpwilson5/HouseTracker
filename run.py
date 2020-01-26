import os

from app import create_app

config_name = os.getenv('FLASK_CONFIG')
app = create_app(config_name)

if __name__ == '__main__':
    app.run()

""" native web server - uses the config.py file """
""" below should automatically happen now when you cd into crm"""

""" heroku local - uses the .env file """
"""
cd crm
source venv/bin/activate
heroku local
heroku open
"""

""" deploy to prod """
"""
cd crm
source venv/bin/activate
git push heroku master
heroku ps:scale web=1
heroku open
"""

"""
cd crm
source venv/bin/activate
export FLASK_CONFIG=development
export FLASK_APP=run.py
export FLASK_DEBUG=true
flask run
"""

""" gunicorn - uses the config.py file """
"""
cd crm
source venv/bin/activate
gunicorn run:app
"""
