from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, login_required, current_user
from app import login_manager
from ..database import mongo
from bson import ObjectId
from pymongo import UpdateOne
import datetime

'''https://code.luasoftware.com/tutorials/flask/how-to-configure-flask-login/'''
'''https://runningcodes.net/flask-login-and-mongodb/'''

class User(UserMixin):
    def __init__(self, id=None, email=None, account=None, superuser=False, active=False, role=None, listing=None):
        self.id = id
        self.email = email
        self.account = account
        self.superuser = superuser
        self.active = active
        self.role = role
        self.listing = listing

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def get_account(self):
        return self.account

    def get_role(self):
        return self.role

    def get_listing(self):
        return self.listing

    @property
    def is_superuser(self):
        return self.superuser

    @staticmethod
    def add(email, first_name, last_name, account_id, role, cell=None, password=None, \
        invited_by=None, confirmed=True, listing='all', email_alert=False, text_alert=False):
        return mongo.db.users.insert({
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'cell': cell,
            'role': role,
            'account': account_id,
            'password': generate_password_hash(password, method='sha256'),
            'email_alert': email_alert,
            'text_alert': text_alert,
            'create_date': datetime.datetime.now().isoformat(),
            'authenticated': False,
            'superuser': False,
            'invited_by': invited_by,
            'active': True,
            'confirmed': confirmed,
            'listing': listing,
            'create_date': datetime.datetime.now().isoformat(),
            'update_date': datetime.datetime.now().isoformat()
        })

    @staticmethod
    def get(id=None, email=None, accounts_realtor=None):
        if id:
            find_by = {'_id': ObjectId(id)}
        elif accounts_realtor:
            find_by = {'account': ObjectId(accounts_realtor), 'role': 'realtor'}
        else:
            find_by = {'email': email}

        return mongo.db.users.find_one(find_by)

    @staticmethod
    def all(account=None, listing=None, email_alert=None, text_alert=None):
        if account:
            find_by = {'account': account, 'active': True}
        else:
            find_by = {'listing': listing, 'active': True}

        if email_alert:
            find_by['email_alert'] = True

        if text_alert:
            find_by['text_alert'] = True

        return mongo.db.users.find(find_by)

    @staticmethod
    def update(id, email, first_name=None, last_name=None, cell=None, password=None, confirmed=None, \
    email_alert=None, text_alert=None, listing=None):
        set = {
            'email': email,
            'update_date': datetime.datetime.now().isoformat()
        }

        # need to append to listing array as the client/partner already has at least one
        if listing:
            mongo.db.users.update_one({
                '_id': ObjectId(id)},{
                '$push': {'listing': listing}
            }, upsert=False)

        # if existing user is being updated so it shouldn't overwrite
        # any information the user had set for themselves
        if first_name:
            set['first_name'] = first_name
        if last_name:
            set['last_name'] = last_name
        if cell:
            set['cell'] = cell
        if confirmed:
            set['confirmed'] = confirmed
        if email_alert:
            set['email_alert'] = email_alert
        if text_alert:
            set['text_alert'] = text_alert
        if password:
            set['password'] = generate_password_hash(password, method='sha256')

        return mongo.db.users.update_one({
            '_id': ObjectId(id)},{
            '$set': set
        }, upsert=False)

    @staticmethod
    def delete(id, context, listing=None):
        if context == 'admin':
            return mongo.db.users.update_one(
                {'_id': ObjectId(id)},
                {'$set': {'active': 'false'}
            }, upsert=False)

        if context == 'client':
            return mongo.db.users.update_one({
                '_id': ObjectId(id)},{
                '$pull': {'listing': listing}
            }, upsert=False)

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)

    # Added this to store login to Mongo #
    def log_login(self):
        return mongo.db.login.insert({
            'user_id': self.id,
            'email': self.email,
            'account': self.account,
            'login_date': datetime.datetime.now().isoformat()
        })

@login_manager.user_loader
def load_user(id):
    users = mongo.db.users.find_one({'_id': ObjectId(id)})
    if not users:
        return None
    return User(str(users['_id']), users['email'], users['account'], users['superuser'], users['active'], users['role'], users['listing'])


class Account(object):
    def __init__(self, name, phone, email):
        self.name = name
        self.phone = phone
        self.email = email

    def add(self):
        return mongo.db.accounts.insert({
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'create_date': datetime.datetime.now().isoformat(),
            'update_date': datetime.datetime.now().isoformat()
        })


class Template(object):
    def __init__(self, name, account):
        self.name = name
        self.account = account

    def add(self):
        return mongo.db.templates.insert({
            'name': self.name,
            'account': self.account,
            'active': 'true',
            'create_date': datetime.datetime.now().isoformat(),
            'update_date': datetime.datetime.now().isoformat()
        })

    @staticmethod
    def get(id):
        return mongo.db.templates.find_one({
            '_id': ObjectId(id)
        })

    @staticmethod
    def all(account):
        return mongo.db.templates.find({
            'account': account,
            'active': 'true'
        }).sort('name',1)

    @staticmethod
    def update(id, name):
        return mongo.db.templates.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'name': name,
                'update_date': datetime.datetime.now().isoformat()
                }
        }, upsert=False)

    @staticmethod
    def delete(id):
        return mongo.db.templates.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'active': 'false'}
        }, upsert=False)


class TemplateStep(object):
    def __init__(self, template_id, name, notes, days_before_close):
        self.template_id = template_id
        self.name = name
        self.notes = notes
        self.days_before_close = days_before_close

    def add(self):
        template = Template.get(self.template_id)
        next_order = template['order'] + 1 if 'order' in template else 1

        return mongo.db.templates.update_one({
            '_id': ObjectId(self.template_id)
        },{
            '$set': { 'update_date': datetime.datetime.now().isoformat() },
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
                    'create_date': datetime.datetime.now().isoformat(),
                    'update_date': datetime.datetime.now().isoformat()
                }
            }
        }, upsert=False)

    @staticmethod
    def get(id, step_id):
        return mongo.db.templates.find_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },
        {'steps.$':1})

    @staticmethod
    def all(id):
        return mongo.db.templates.aggregate([
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
        return mongo.db.templates.update_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },{
            '$set': {
                'steps.$.name': name,
                'steps.$.notes': notes,
                'steps.$.days_before_close': days_before_close,
                'steps.$.update_date': datetime.datetime.now().isoformat()
            }
        }, upsert=False)

    @staticmethod
    def delete(id, step_id):
        return mongo.db.templates.update_one({
            '_id': ObjectId(id),
            'steps._id': ObjectId(step_id)
        },{
            '$set': {
                'steps.$.active': False,
                'steps.$.update_date': datetime.datetime.now().isoformat()
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

        return mongo.db.templates.bulk_write(operations)
