from ..database import mongo
from flask_login import login_required, current_user
from bson import ObjectId
import datetime

class AppStep(object):
    def __init__(self, name, notes, days_before_close):
        self.name = name
        self.notes = notes
        self.days_before_close = days_before_close
        self.user = current_user.get_id()

    def add(self):
        return mongo.db.appsteps.insert({
            'name': self.name,
            'notes': self.notes,
            'days_before_close': self.days_before_close,
            'user': self.user,
            'active': 'true',
            'create_date': datetime.datetime.now().isoformat(),
            'update_date': datetime.datetime.now().isoformat()
        })

    def count(self):
        return self.count(True)

    @staticmethod
    def get(id):
        return mongo.db.appsteps.find_one({
            '_id': ObjectId(id)
        })

    @staticmethod
    def all():
        return mongo.db.appsteps.find({
            'active': 'true'
        })

    @staticmethod
    def update(id, name, notes, days_before_close):
        return mongo.db.appsteps.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'name': name,
                'notes': notes,
                'days_before_close': days_before_close,
                'update_date': datetime.datetime.now().isoformat()
                }
        }, upsert=False)

    @staticmethod
    def delete(id):
        return mongo.db.appsteps.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'active': 'false'}
        }, upsert=False)
