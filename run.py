import os

from app import create_app

config_name = os.getenv('FLASK_CONFIG')
app = create_app(config_name)

if __name__ == '__main__':
    app.run()

""" native web server - uses the config.py file """
""" below should automatically happen now when you cd into housetracker"""
"""
cd housetracker
source venv/bin/activate
export FLASK_CONFIG=development
export FLASK_APP=run.py
export FLASK_DEBUG=true
flask run
"""

""" gunicorn - uses the config.py file """
"""
cd housetracker
source venv/bin/activate
gunicorn run:app
"""

""" heroku local - uses the .env file """
"""
cd housetracker
source venv/bin/activate
"""

""" deploy to prod """
"""
cd housetracker
source venv/bin/activate
git push heroku master
heroku ps:scale web=1
heroku open
"""
