from flask_pymongo import PyMongo
import os

mongo = PyMongo(os.environ.get('MONGO_URI'))
