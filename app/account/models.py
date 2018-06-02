from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, login_required, current_user
from app import login_manager
from ..database import mongo
from bson import ObjectId
import datetime

'''https://code.luasoftware.com/tutorials/flask/how-to-configure-flask-login/'''
'''https://runningcodes.net/flask-login-and-mongodb/'''

class User(UserMixin):
    def __init__(self, id=None, email=None, account=None, superuser=False, active=False):
        self.id = id
        self.email = email
        self.account = account
        self.superuser = superuser
        self.active = active

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

    @property
    def is_superuser(self):
        return self.superuser

    @staticmethod
    def add(first_name, last_name, email, account_id, role, cell=None, password=None, invited_by=None, confirmed=True, listing='All'):
        return mongo.db.users.insert({
            'firstname': first_name,
            'lastname': last_name,
            'email': email,
            'cell': cell,
            'role': role,
            'account': account_id,
            'password': generate_password_hash(password, method='sha256'),
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
    def get(id=None, email=None):
        if id:
            return mongo.db.users.find_one({
                '_id': ObjectId(id)
            })
        else:
            return mongo.db.users.find_one({
                'email': email
            })

    @staticmethod
    def all(account=None, listing=None):
        if account:
            return mongo.db.users.find({
                'account': account,
                'active': True
            })
        else:
            return mongo.db.users.find({
                'listing': listing,
                'active': True
            })

    @staticmethod
    def update(id, first_name, last_name, email, cell=None, password=None, confirmed=False):
        return mongo.db.users.update_one({
            '_id': ObjectId(id)},{
            '$set': {
                    'firstname': first_name,
                    'lastname': last_name,
                    'email': email,
                    'cell': cell,
                    'confirmed':confirmed,
                    'password': generate_password_hash(password, method='sha256'),
                    'update_date': datetime.datetime.now().isoformat()
                }
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
    return User(str(users['_id']), users['email'], users['account'], users['superuser'], users['active'])


class Account(object):
    def __init__(self, name, phone, email):
        self.name = 'namevalue'
        self.phone = 'phonevalue'
        self.email = 'emailvavlue'

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
    def __init__(self, name, notes, account):
        self.name = name
        self.notes = notes
        self.account = account

    def add(self):
        return mongo.db.steps.insert({
            'name': self.name,
            'notes': self.notes,
            'account': self.account,
            'active': 'true',
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
        })

    @staticmethod
    def update(id, name, notes):
        return mongo.db.steps.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'name': name,
                'notes': notes,
                'update_date': datetime.datetime.now().isoformat()
                }
        }, upsert=False)

    @staticmethod
    def delete(id):
        return mongo.db.steps.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'active': 'false'}
        }, upsert=False)
