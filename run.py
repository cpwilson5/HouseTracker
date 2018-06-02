import os

from app import create_app

config_name = os.getenv('FLASK_CONFIG')
app = create_app(config_name)

if __name__ == '__main__':
    app.run()

"""
cd housetracker
export FLASK_CONFIG=development
export FLASK_APP=run.py
export FLASK_DEBUG=true
flask run
"""
