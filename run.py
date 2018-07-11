import os

from app import create_app

config_name = os.getenv('FLASK_CONFIG')
app = create_app(config_name)

if __name__ == '__main__':
    app.run()

"""
--> below should automatically happen now when you cd into housetracker <--
cd housetracker
source venv/bin/activate
export FLASK_CONFIG=development
export FLASK_APP=run.py
export FLASK_DEBUG=true
flask run
"""
