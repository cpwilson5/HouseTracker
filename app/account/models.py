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
    def add(first_name, last_name, email, account_id, role, cell=None, password=None, \
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
            print find_by
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
    def update(id, first_name, last_name, email, cell=None, password=None, confirmed=False, \
    email_alert=False, text_alert=False):
        set = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'cell': cell,
            'confirmed':confirmed,
            'email_alert': email_alert,
            'text_alert': text_alert,
            'update_date': datetime.datetime.now().isoformat()
        }

        if password:
            set['password'] = generate_password_hash(password, method='sha256')

        return mongo.db.users.update_one({
            '_id': ObjectId(id)},{
            '$set': set
        }, upsert=False)

    @staticmethod
    def delete(id):
        return mongo.db.users.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'active': 'false'}
        }, upsert=False)

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)

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

    '''def get(self):
        return mongo.db.steps.find_one({
            '_id': ObjectId(id)
        })

    @staticmethod
    def all():
        return mongo.db.steps.find({
            'user': current_user.get_id(),
            'active': 'true'
        })

    @staticmethod
    def update(id, form):
        return mongo.db.steps.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'name': self.name, 'update_date': datetime.datetime.now().isoformat()}
        }, upsert=False)

    @staticmethod
    def delete(id):
        return mongo.db.steps.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'active': 'false'}
        }, upsert=False)'''


class Step(object):
    def __init__(self, name, notes, days_before_close, account):
        self.name = name
        self.notes = notes
        self.days_before_close = days_before_close
        self.account = account

    def add(self):
        next_order = mongo.db.steps.count({
            'account': self.account,
            'active': 'true'
        })

        return mongo.db.steps.insert({
            'name': self.name,
            'notes': self.notes,
            'days_before_close': self.days_before_close,
            'account': self.account,
            'active': 'true',
            'order': next_order + 1,
            'create_date': datetime.datetime.now().isoformat(),
            'update_date': datetime.datetime.now().isoformat()
        })

    @staticmethod
    def get(id):
        return mongo.db.steps.find_one({
            '_id': ObjectId(id)
        })

    @staticmethod
    def all(account):
        return mongo.db.steps.find({
            'account': account,
            'active': 'true'
        }).sort('order', 1)

    @staticmethod
    def update(id, name, notes, days_before_close):
        return mongo.db.steps.update_one(
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
        return mongo.db.steps.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'active': 'false'}
        }, upsert=False)

    @staticmethod
    def sort(account_id, step_ids):
        steps = step_ids.split(',')
        operations = []
        order = 1

        for step_id in steps:
            operations.append(UpdateOne({
                    '_id': ObjectId(step_id),
                    'account': ObjectId(account_id)
                },{
                    '$set': {
                        'order': order
                    }
                }, upsert=False))

            order += 1

        return mongo.db.steps.bulk_write(operations)
