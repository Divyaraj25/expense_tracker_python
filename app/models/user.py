from datetime import datetime
import bcrypt
from flask_login import UserMixin
from app import mongo, login_manager
from bson import ObjectId

@login_manager.user_loader
def load_user(user_id):
    user_data = User.find_by_id(user_id)
    if not user_data:
        return None
    return User(user_data)

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.password_hash = user_data['password']
        self.created_at = user_data.get('created_at', datetime.now())
        self.updated_at = user_data.get('updated_at', datetime.now())

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    @staticmethod
    def create(username, email, password):
        # Generate salt and hash password using bcrypt
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        user = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        result = mongo.db.users.insert_one(user)
        return str(result.inserted_id)

    @staticmethod
    def find_by_username(username):
        return mongo.db.users.find_one({'username': username})

    @staticmethod
    def find_by_email(email):
        return mongo.db.users.find_one({'email': email})

    @staticmethod
    def find_by_id(user_id):
        return mongo.db.users.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def verify_password(stored_password, provided_password):
        # Ensure stored_password is bytes (as stored in MongoDB)
        if isinstance(stored_password, str):
            stored_password = stored_password.encode('utf-8')
        
        # Check password using bcrypt
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

    def check_password(self, password):
        # Check password using bcrypt
        if isinstance(self.password_hash, str):
            stored_password = self.password_hash.encode('utf-8')
        else:
            stored_password = self.password_hash
            
        return bcrypt.checkpw(password.encode('utf-8'), stored_password)

    @staticmethod
    def update_user(user_id, update_data):
        update_data['updated_at'] = datetime.now()
        return mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})