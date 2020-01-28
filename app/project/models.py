from ..database import mongo
from flask_login import login_required, current_user
from bson import ObjectId
from pymongo import UpdateOne
import datetime

class Project(object):
    def __init__(self, name, address1, address2, city, state, zip, close_date, photo=None):
        self.name = name
        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.state = state
        self.zip = zip
        self.close_date = close_date
        self.photo = photo

    def add(self):
        ### Enables no closing date to be added when project is created ###
        if self.close_date is None:
            close_date = ''
        else:
            close_date = self.close_date

        return mongo.db.projects.insert({
            'name': self.name,
            'address1': self.address1,
            'address2': self.address2,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'close_date': close_date,
            'photo': self.photo,
            'user': current_user.get_id(),
            'account': current_user.get_account(),
            'active': True,
            'steps': [],
            'create_date': datetime.datetime.utcnow(),
            'update_date': datetime.datetime.utcnow()
        })

    @staticmethod
    def get(id):
        return mongo.db.projects.find_one({
            '_id': ObjectId(id)
        })

    @staticmethod
    def all(active=True, complete=False, sort='update_date', order=-1):
        get = {
            'active': active
        }

        if complete == False: #this is the default and the projects results
            get['complete_date'] = { '$exists': complete }
        else: #this limits to the last 30 days until we build paging
            thirty_days_before = datetime.datetime.today() - datetime.timedelta(days=30)
            get['complete_date'] = { '$gte' : datetime.datetime(2018, 7, 5) }

        if current_user.get_project() == 'all': # realtor/admin's projects
            get['account'] = current_user.get_account()
            return mongo.db.projects.find(get).sort(sort,order)

        else: # it's a client/partner
            projects_to_retrieve = current_user.get_project()
            projects_to_retrieve = [ObjectId(s) for s in projects_to_retrieve]
            get['_id'] = { '$in': projects_to_retrieve }
            return mongo.db.projects.find(get).sort(sort,order)

    @staticmethod
    def update(id, name, address1, address2, city, state, zip, close_date, photo):
        project = Project.get(id)
        if photo is None:
            photo = project['photo'] if 'photo' in project else None

        return mongo.db.projects.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'name': name,
                'address1': address1,
                'address2': address2,
                'city': city,
                'state': state,
                'zip': zip,
                'close_date': close_date,
                'photo': photo,
                'update_date': datetime.datetime.utcnow()
                }
        }, upsert=False)

    @staticmethod
    def delete(id):
        return mongo.db.projects.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'active': False,
                'update_date': datetime.datetime.utcnow()
            }
        }, upsert=False)

    @staticmethod
    def complete(id):
        return mongo.db.projects.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'complete_date': datetime.datetime.utcnow(),
                'update_date': datetime.datetime.utcnow()
            }
        }, upsert=False)

    @staticmethod
    def reactivate(id):
        return mongo.db.projects.update_one(
            {'_id': ObjectId(id)},
            {
                '$unset': {
                    'complete_date': '',
                },
                '$set': {
                    'update_date': datetime.datetime.utcnow()
                }
        }, upsert=False)


class ProjectStep(object):
    def __init__(self, project_id, name, notes, attachment=None, due_date=None, order=0, status=None):
        self.project_id = project_id
        self.name = name
        self.notes = notes
        self.attachment = attachment
        self.due_date = due_date
        self.status = status

    def add(self):
        ### Enables app steps (no dates) to be added when project is created ###
        if self.due_date is None:
            due_date = ''
        else:
            due_date = self.due_date

        # because there is an array of objects (aka hard to get to what we need) and we need to ensure we
        # add the next step to the end, we stored a project step count on the project itself
        project = Project.get(self.project_id)
        next_order = project['order'] + 1 if 'order' in project else 1

        return mongo.db.projects.update_one({
            '_id': ObjectId(self.project_id)
        },{
            '$set': { 'update_date': datetime.datetime.utcnow() },
            '$inc': {'order': 1}, #increment the project order count to keep track of # of project steps
            '$push': {
                'steps':
                {
                    '_id': ObjectId(),
                    'name': self.name,
                    'notes': self.notes,
                    'attachment': self.attachment,
                    'due_date': due_date,
                    'status': self.status,
                    'active': True,
                    'order': next_order, #set the new project step to the next number
                    'create_date': datetime.datetime.utcnow(),
                    'update_date': datetime.datetime.utcnow()
                }
            }
        }, upsert=False)

    def count(self):
        return list(mongo.db.projects.aggregate([{
            '$project':
            {
                '_id': 1,
                'numberOfSteps': { '$size': '$steps' }
            }
        }]))

    @staticmethod
    def get(id, step_id):
        return mongo.db.projects.find_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },
        {'steps.$':1})

    @staticmethod
    def all(id, active=True, include_complete=True):
        match = {
            '_id' : ObjectId(id),
            'steps.active': active
        }

        if include_complete == False:
            match['steps.complete_date'] = { '$exists': False }

        return mongo.db.projects.aggregate([
            { '$unwind' : '$steps' },
            { '$match' : match },
            { '$sort' : { 'steps.order' : 1 } }
        ])

    @staticmethod
    def update(id, step_id, name, notes, attachment, due_date, status):
        if attachment is None:
            attachment = ProjectStep.get(id, step_id)['steps'][0]['attachment']

        return mongo.db.projects.update_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },{
            '$set': {
                'steps.$.name': name,
                'steps.$.notes': notes,
                'steps.$.attachment': attachment,
                'steps.$.due_date': due_date,
                'steps.$.status': status,
                'steps.$.update_date': datetime.datetime.utcnow(),
                'update_date': datetime.datetime.utcnow()
            }
        }, upsert=False)

    @staticmethod
    def delete(id, step_id):
        return mongo.db.projects.update_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },{
            '$set': {
                'steps.$.active': False,
                'steps.$.update_date': datetime.datetime.utcnow(),
                'update_date': datetime.datetime.utcnow()
            }
        }, upsert=False)

    @staticmethod
    def complete(id, step_id):
        return mongo.db.projects.update_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },{
            '$set': {
                'steps.$.complete_date': datetime.datetime.utcnow(),
                'steps.$.update_date': datetime.datetime.utcnow(),
                'update_date': datetime.datetime.utcnow()
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

        return mongo.db.projects.bulk_write(operations)
