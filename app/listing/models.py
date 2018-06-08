from ..database import mongo
from flask_login import login_required, current_user
from bson import ObjectId
from pymongo import UpdateOne
import datetime

class Listing(object):
    def __init__(self, name, address1, address2, city, state, zip, close_date):
        self.name = name
        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.state = state
        self.zip = zip
        self.close_date = close_date

    def add(self):
        return mongo.db.listings.insert({
            'name': self.name,
            'address1': self.address1,
            'address2': self.address2,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'close_date': datetime.datetime.combine(self.close_date, datetime.time.min).isoformat(),
            'user': current_user.get_id(),
            'account': current_user.get_account(),
            'active': True,
            'steps': [],
            'create_date': datetime.datetime.now().isoformat(),
            'update_date': datetime.datetime.now().isoformat()
        })

    @staticmethod
    def get(id):
        return mongo.db.listings.find_one({
            '_id': ObjectId(id)
        })

    @staticmethod
    def all(active=True, complete=False, sort='create_date', order=-1):
        return mongo.db.listings.find({
            'account': current_user.get_account(),
            'active': active,
            'complete_date' : { '$exists': complete }
        }).sort(sort,order)

    @staticmethod
    def update(id, name, address1, address2, city, state, zip, close_date):
        return mongo.db.listings.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'name': name,
                'address1': address1,
                'address2': address2,
                'city': city,
                'state': state,
                'zip': zip,
                'close_date': datetime.datetime.combine(close_date, datetime.time.min).isoformat(),
                'update_date': datetime.datetime.now().isoformat()
                }
        }, upsert=False)

    @staticmethod
    def delete(id):
        return mongo.db.listings.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'active': False,
                'update_date': datetime.datetime.now().isoformat()
            }
        }, upsert=False)

    @staticmethod
    def complete(id):
        return mongo.db.listings.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'complete_date': datetime.datetime.now().isoformat(),
                'update_date': datetime.datetime.now().isoformat()
            }
        }, upsert=False)


class ListingStep(object):
    def __init__(self, listing_id, name, notes, attachment=None, due_date=None, order=0, color=None):
        self.listing_id = listing_id
        self.name = name
        self.notes = notes
        self.attachment = attachment
        self.due_date = due_date
        self.color = color

    def add(self):
        ### Enables app steps (no dates) to be added when listing is created ###
        if self.due_date is None:
            due_date = ''
        else:
            due_date = datetime.datetime.combine(self.due_date, datetime.time.min)

        listing = Listing.get(self.listing_id)
        next_order = listing['order'] + 1 if 'order' in listing else 1

        return mongo.db.listings.update_one({
            '_id': ObjectId(self.listing_id)
        },{
            '$set': { 'update_date': datetime.datetime.now().isoformat() },
            '$inc': {'order': 1},
            '$push': {
                'steps':
                {
                    '_id': ObjectId(),
                    'name': self.name,
                    'notes': self.notes,
                    'attachment': self.attachment,
                    'due_date': due_date,
                    'color': self.color,
                    'active': True,
                    'order': next_order,
                    'create_date': datetime.datetime.now().isoformat(),
                    'update_date': datetime.datetime.now().isoformat()
                }
            }
        }, upsert=False)

    def count(self):
        return list(mongo.db.listings.aggregate([{
            '$project':
            {
                '_id': 1,
                'numberOfSteps': { '$size': '$steps' }
            }
        }]))

    @staticmethod
    def get(id, step_id):
        return mongo.db.listings.find_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },
        {'steps.$':1})

    @staticmethod
    def all(id, active=True, complete=False):
        return mongo.db.listings.aggregate([
            { '$unwind' : '$steps' },
            { '$match' : {
                '_id' : ObjectId(id),
                'steps.active': active,
                'steps.complete_date' : { '$exists': complete }
                }
            },
            { '$sort' : { 'steps.order' : 1 } }
        ])

    @staticmethod
    def update(id, step_id, name, notes, attachment, due_date, color):
        if due_date is None:
            due_date = ''
        else:
            due_date = datetime.datetime.combine(due_date, datetime.time.min)

        if attachment is None:
            attachment = ListingStep.get(id, step_id)['steps'][0]['attachment']

        return mongo.db.listings.update_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },{
            '$set': {
                'steps.$.name': name,
                'steps.$.notes': notes,
                'steps.$.attachment': attachment,
                'steps.$.due_date': due_date,
                'steps.$.color': color,
                'steps.$.update_date': datetime.datetime.now().isoformat(),
                'update_date': datetime.datetime.now().isoformat()
            }
        }, upsert=False)

    @staticmethod
    def delete(id, step_id):
        return mongo.db.listings.update_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },{
            '$set': {
                'steps.$.active': False,
                'steps.$.update_date': datetime.datetime.now().isoformat(),
                'update_date': datetime.datetime.now().isoformat()
            }
        }, upsert=False)

    @staticmethod
    def complete(id, step_id):
        return mongo.db.listings.update_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },{
            '$set': {
                'steps.$.complete_date': datetime.datetime.now().isoformat(),
                'steps.$.update_date': datetime.datetime.now().isoformat(),
                'update_date': datetime.datetime.now().isoformat()
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

        return mongo.db.listings.bulk_write(operations)
