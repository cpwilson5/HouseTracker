from ..database import mongo
from flask_login import login_required, current_user
from bson import ObjectId
from pymongo import UpdateOne
import datetime

class AppTemplate(object):
    def __init__(self, name):
        self.name = name
        self.user = current_user.get_id()

    def add(self):
        return mongo.db.apptemplates.insert({
            'name': self.name,
            'active': 'true',
            'user': self.user,
            'create_date': datetime.datetime.utcnow(),
            'update_date': datetime.datetime.utcnow()
        })

    @staticmethod
    def get(id):
        return mongo.db.apptemplates.find_one({
            '_id': ObjectId(id)
        })

    @staticmethod
    def all():
        return mongo.db.apptemplates.find({
            'active': 'true'
        }).sort('name',1)

    @staticmethod
    def update(id, name):
        return mongo.db.apptemplates.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'name': name,
                'update_date': datetime.datetime.utcnow()
                }
        }, upsert=False)

    @staticmethod
    def delete(id):
        return mongo.db.apptemplates.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'active': 'false'}
        }, upsert=False)


class AppTemplateStep(object):
    def __init__(self, template_id, name, notes, days_before_close):
        self.template_id = template_id
        self.name = name
        self.notes = notes
        self.days_before_close = days_before_close

    def add(self):
        template = AppTemplate.get(self.template_id)
        next_order = template['order'] + 1 if 'order' in template else 1

        return mongo.db.apptemplates.update_one({
            '_id': ObjectId(self.template_id)
        },{
            '$set': { 'update_date': datetime.datetime.utcnow() },
            '$inc': {'order': 1}, #increment the listing order count to keep track of # of listing steps
            '$push': {
                'steps':
                {
                    '_id': ObjectId(),
                    'name': self.name,
                    'notes': self.notes,
                    'days_before_close': self.days_before_close,
                    'active': True,
                    'order': next_order, #set the new listing step to the next number
                    'create_date': datetime.datetime.utcnow(),
                    'update_date': datetime.datetime.utcnow()
                }
            }
        }, upsert=False)

    @staticmethod
    def get(id, step_id):
        return mongo.db.apptemplates.find_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },
        {'steps.$':1})

    @staticmethod
    def all(id):
        return mongo.db.apptemplates.aggregate([
            { '$unwind' : '$steps' },
            { '$match' : {
                '_id' : ObjectId(id),
                'steps.active': True,
                }
            },
            { '$sort' : { 'steps.order' : 1 } }
        ])

    @staticmethod
    def update(id, step_id, name, notes, days_before_close):
        return mongo.db.apptemplates.update_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },{
            '$set': {
                'steps.$.name': name,
                'steps.$.notes': notes,
                'steps.$.days_before_close': days_before_close,
                'steps.$.update_date': datetime.datetime.utcnow()
            }
        }, upsert=False)

    @staticmethod
    def delete(id, step_id):
        return mongo.db.apptemplates.update_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },{
            '$set': {
                'steps.$.active': False,
                'steps.$.update_date': datetime.datetime.utcnow()
            }
        }, upsert=False)

    @staticmethod
    def sort(id, step_ids):
        steps = step_ids.split(',')
        operations = []
        order = 1

        for step_id in steps:
            operations.append(UpdateOne({
                    '_id': ObjectId(id),
                    'steps._id': ObjectId(step_id)
                },{
                    '$set': {
                        'steps.$.order': order
                    }
                }, upsert=False))

            order += 1

        return mongo.db.apptemplates.bulk_write(operations)
